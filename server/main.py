#!/usr/bin/env python3
"""JKM LCD control server + display loop (stdlib only)."""
from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

try:
    from . import sensors, display, animations, sound, pairing
except ImportError:  # running as a script
    import sensors, display, animations, sound, pairing

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
CONF = pairing.load_config()
HOST = os.environ.get("JKM_HOST", CONF.get("host", "0.0.0.0"))
PORT = int(os.environ.get("JKM_PORT", CONF.get("port", 8090)))
REQUIRE_TOKEN = (os.environ.get("JKM_REQUIRE_TOKEN", "").lower() in ("1", "true", "yes")
                 or bool(CONF.get("require_token")))
VERSION = "3.1"
STATE_FILE = Path(os.environ.get("JKM_STATE_FILE", "/var/lib/jkm-lcd/state.json"))


def _load_saved() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _save_current():
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({
            "mode": STATE.mode,
            "animation": STATE.animation,
            "display_on": STATE.display_on,
        }))
    except Exception:
        pass  # настройки не критичны: работаем и без файла


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.mode = "temp"
        self.animation = "wave"
        self.display_on = True
        self.volume = None
        self.playing = False
        self.level = 0
        self.auto_prev = None     # режим, куда вернуться после «Звука»
        self.auto_until = 0.0
        self.raw = None           # (bytes, until_ts) — диагностика протокола
        self.ttype = 0            # последний отправленный тип (вкладка)
        self.flag_power = False   # 0x80 — левая вкладка
        self.latest = {
            "temp": None, "power": None, "load": 0, "clock": 0, "gpu": 0,
            "flags": 0x40, "connected": False, "port": None,
            "display_on": True,
        }
        self.started = time.time()


STATE = State()
_saved = _load_saved()
if _saved.get("mode") in animations.MODES:
    STATE.mode = _saved["mode"]
if _saved.get("animation") in animations.ANIMATIONS:
    STATE.animation = _saved["animation"]
if isinstance(_saved.get("display_on"), bool):
    STATE.display_on = _saved["display_on"]


def display_loop():
    """Кадры на экран. Любая ошибка не должна убивать поток: раньше
    исключение в кадре тихо останавливало индикацию."""
    disp = display.JkmDisplay()
    sens = sensors.Sensors()
    level = sound.Level()
    level.start()
    state = {"last_poll": 0.0, "last_volume": None}

    def step():
        with STATE.lock:
            display_on = STATE.display_on

        # Экран выключен: закрываем порт и не отправляем ничего. При закрытии
        # CDC-порта кулер гасит индикацию (так же ведёт себя вендорская
        # утилита). Порт держать открытым нельзя: после долгой тишины
        # прошивка не принимает кадры без нового handshake, и «включить»
        # обратно не получалось (#857).
        if not display_on:
            if disp.fd is not None:
                # Прошивка гаснет не мгновенно после тишины (~10 с), но
                # нулевой кадр перед закрытием убирает хотя бы шкалу.
                disp.send(0, 0, 0, 0, 0, 0, 0, 0)
                time.sleep(0.05)
                disp.close()
            snap = sens.snapshot()
            with STATE.lock:
                STATE.latest = {
                    **snap,
                    "flags": 0,
                    "display_temp": 0,
                    "display_power": 0,
                    "display_load": 0,
                    "display_on": False,
                    "panel_lit": False,
                    "connected": False,
                    "port": None,
                }
            time.sleep(0.5)
            return

        # Включён: открываем порт заново (connect делает handshake) и шлём
        # кадры. Это и есть «разбудить» экран после выключения.
        if disp.fd is None:
            if not disp.connect():
                with STATE.lock:
                    STATE.latest = {**STATE.latest, "connected": False}
                time.sleep(1)
                return

        # Диагностика: временно шлём произвольные байты (см. /api/raw).
        if STATE.raw:
            data, until = STATE.raw
            if time.time() < until:
                disp.send_bytes(data)
                time.sleep(0.1)
                return
            STATE.raw = None

        snap = sens.snapshot()

        # Звук: громкость и уровень. Пока крутят громкость — на 5 секунд
        # сами переходим в режим «Звук» и потом возвращаемся.
        now = time.time()
        if now - state["last_poll"] >= 0.5:
            vol = sound.volume()
            play = level.active
            if vol is not None:
                if state["last_volume"] is not None and vol != state["last_volume"]:
                    if STATE.mode != "volume":
                        STATE.auto_prev = STATE.mode
                        STATE.mode = "volume"
                    STATE.auto_until = now + 5.0
                state["last_volume"] = vol
            if STATE.auto_prev and now > STATE.auto_until and STATE.mode == "volume":
                STATE.mode = STATE.auto_prev or "temp"
                STATE.auto_prev = None
            STATE.volume = vol
            STATE.playing = play
            STATE.level = level.value
            state["last_poll"] = now

        snap["volume"] = STATE.volume
        snap["playing"] = STATE.playing
        snap["level"] = STATE.level

        with STATE.lock:
            mode = STATE.mode
            animation = STATE.animation

        # RAPL needs two readings and coretemp may need a moment: never send
        # a frame with placeholder values, wait for real data instead.
        if snap["temp"] is None or snap["power"] is None:
            with STATE.lock:
                STATE.latest = {
                    **snap,
                    "display_on": True,
                    "connected": disp.fd is not None,
                    "port": disp.path,
                }
            time.sleep(0.1)
            return

        vals = animations.render(mode, animation, time.time(), snap)
        if vals["blackout"]:
            ok = disp.send(0, 0, 0, 0, 0, 0, 0, 0)
        else:
            ok = disp.send(vals["temp"], vals["load"], vals["flags"],
                           display.RPM_PLACEHOLDER, vals["clk"],
                           vals["pwr"], snap["gpu"], vals["ttype"])

        with STATE.lock:
            STATE.ttype = vals["ttype"]
            STATE.flag_power = bool(vals["flags"] & 0x80)
            STATE.latest = {
                **snap,
                "flags": vals["flags"],
                "ttype": vals["ttype"],
                "display_temp": vals["temp"],
                "display_power": vals["pwr"],
                "display_load": vals["load"],
                "display_on": True,
                "panel_lit": not vals["blackout"],
                "connected": ok and disp.fd is not None,
                "port": disp.path,
            }
        # Vendor sends a 13-byte frame every 100 ms; same cadence makes
        # animations and mode changes smooth.
        time.sleep(0.1)

    while True:
        try:
            step()
        except Exception:
            import traceback
            traceback.print_exc()
            time.sleep(1)


class Handler(BaseHTTPRequestHandler):
    server_version = "jkm-lcd/3.1"

    def log_message(self, fmt, *args):
        # quieter logs
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        try:
            n = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(n) if n else b"{}"
            return json.loads(raw.decode() or "{}")
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _authorized(self) -> bool:
        if not REQUIRE_TOKEN:
            return True
        if self.client_address[0] in ("127.0.0.1", "::1"):
            return True
        token = self.headers.get("X-JKM-Token", "")
        return bool(token) and pairing.verify(token)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            with STATE.lock:
                return self._json(200, {
                    "ok": True, "service": "jkm-lcd", "version": VERSION,
                    "connected": STATE.latest.get("connected", False),
                })
        if path.startswith("/api/") and path not in (
                "/api/pair/code", "/api/pair/devices") and not self._authorized():
            return self._json(401, {"error": "not paired"})
        if path == "/api/pair/code":
            info = pairing.new_code()
            info["url"] = f"http://{self.headers.get('Host', '192.168.31.100:8090')}/"
            return self._json(200, info)
        if path == "/api/pair/devices":
            return self._json(200, {"items": pairing.devices()})
        if path == "/api/status":
            with STATE.lock:
                payload = {
                    "version": VERSION,
                    "mode": STATE.mode,
                    "animation": STATE.animation,
                    "display_on": STATE.display_on,
                    "ttype": STATE.ttype,
                    "tab": ("left" if STATE.flag_power else
                            "center" if STATE.ttype else "right"),
                    "uptime": round(time.time() - STATE.started, 1),
                    "modes": animations.MODES,
                    "animations": animations.ANIMATIONS,
                    "animation_params": animations.ANIMATION_PARAMS,
                    "sound": {
                        "volume": STATE.volume,
                        "playing": STATE.playing,
                        "level": STATE.level,
                    },
                    "sensors": STATE.latest,
                }
            return self._json(200, payload)
        if path == "/api/sensors":
            with STATE.lock:
                return self._json(200, STATE.latest)
        if path == "/api/config":
            with STATE.lock:
                return self._json(200, {
                    "mode": STATE.mode, "animation": STATE.animation,
                    "display_on": STATE.display_on,
                    "modes": animations.MODES, "animations": animations.ANIMATIONS,
                })
        return self._static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self._read_json()
        if path.startswith("/api/") and path != "/api/pair" and not self._authorized():
            return self._json(401, {"error": "not paired"})
        if path == "/api/pair":
            try:
                return self._json(200, pairing.redeem(
                    str(data.get("code", "")), str(data.get("label", ""))))
            except ValueError as e:
                return self._json(400, {"error": str(e)})
        if path == "/api/pair/revoke":
            return self._json(200, {"removed": pairing.revoke(str(data.get("token", "")))})
        if path == "/api/mode":
            mode = str(data.get("mode", ""))
            if mode == "sound":  # обратная совместимость со старыми APK
                mode = "volume"
            if mode not in animations.MODES:
                return self._json(400, {"error": "bad mode",
                                        "modes": animations.MODES})
            with STATE.lock:
                STATE.mode = mode
                STATE.auto_prev = None
                _save_current()
            return self._json(200, {"ok": True, "mode": mode})
        if path == "/api/animation":
            anim = str(data.get("animation", ""))
            if anim not in animations.ANIMATIONS:
                return self._json(400, {"error": "bad animation",
                                        "animations": animations.ANIMATIONS})
            with STATE.lock:
                STATE.animation = anim
                _save_current()
            return self._json(200, {"ok": True, "animation": anim})
        if path == "/api/display":
            if "on" in data:
                on = bool(data.get("on"))
            elif str(data.get("state", "")).lower() in ("on", "off"):
                on = str(data["state"]).lower() == "on"
            else:
                return self._json(400, {"error": "need {\"on\": true|false}"})
            with STATE.lock:
                STATE.display_on = on
                _save_current()
            return self._json(200, {"ok": True, "display_on": on})
        if path == "/api/raw":
            hexstr = str(data.get("hex", "")).replace(" ", "").replace(",", "")
            try:
                payload = bytes.fromhex(hexstr)
            except ValueError:
                return self._json(400, {"error": "hex expected"})
            if not payload or len(payload) > 20:
                return self._json(400, {"error": "1..20 bytes"})
            seconds = max(0.2, min(30.0, float(data.get("seconds", 3))))
            STATE.raw = (payload, time.time() + seconds)
            return self._json(200, {"ok": True, "bytes": len(payload),
                                    "seconds": seconds})
        if path in ("/api/brightness",):
            # Яркость прошивка не умеет: вендорская утилита её не отправляет.
            return self._json(410, {"error": "brightness is not supported by the firmware"})
        if path == "/api/config":
            with STATE.lock:
                mode = data.get("mode")
                if mode == "sound":
                    mode = "volume"
                if mode in animations.MODES:
                    STATE.mode = mode
                if data.get("animation") in animations.ANIMATIONS:
                    STATE.animation = data["animation"]
                if "on" in data:
                    STATE.display_on = bool(data.get("on"))
                _save_current()
                return self._json(200, {
                    "mode": STATE.mode, "animation": STATE.animation,
                    "display_on": STATE.display_on,
                })
        return self._json(404, {"error": "not found"})

    def _static(self, path: str):
        if path in ("", "/"):
            path = "/index.html"
        rel = posixpath.normpath(path).lstrip("/")
        target = (WEB / rel).resolve()
        if not str(target).startswith(str(WEB.resolve())) or not target.is_file():
            return self._json(404, {"error": "not found"})
        data = target.read_bytes()
        ctype = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text/") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(data)


def main():
    threading.Thread(target=display_loop, daemon=True).start()
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"JKM LCD server {VERSION} on http://{HOST}:{PORT}  (web: {WEB})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
