#!/usr/bin/env python3
"""jkmctl — управление пультом JKM LCD с компьютера (Python stdlib).

  jkmctl status | sensors | mode CPU|GPU|Часы|Громкость
  jkmctl anim волна|пинг-понг|дыхание|cpu|gpu|volume|eq|пусто
  jkmctl on | off
  jkmctl pair          — 4-значный код + QR для телефона
  jkmctl devices | revoke <префикс>
  jkmctl require-token on|off
  jkmctl config [host=…] [port=…] [token=…] [show]
  jkmctl doctor
  jkmctl test          — 10 секунд тестового кадра (42 °C, шкала 50 %)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

_HOME = "/home/Arch" if Path("/home/Arch").is_dir() else str(Path.home())
CONF = Path(os.environ.get("JKM_CONFIG", str(Path(_HOME) / ".config/jkm-lcd/config.json")))

MODES = {"cpu": "temp", "temp": "temp", "gpu": "gpu", "часы": "clock",
         "clock": "clock", "звук": "volume", "volume": "volume", "громкость": "volume"}
ANIMS = {"волна": "wave", "wave": "wave", "пинг-понг": "pingpong", "pingpong": "pingpong",
         "дыхание": "breathe", "breathe": "breathe", "cpu": "cputemp", "gpu": "gputemp",
         "шкала-cpu": "cputemp", "шкала-gpu": "gputemp", "громкость": "volume",
         "volume": "volume", "eq": "eq", "эквалайзер": "eq", "пусто": "none", "none": "none"}


def load() -> dict:
    try:
        return json.loads(CONF.read_text())
    except Exception:
        return {"host": "127.0.0.1", "port": 8090, "token": ""}


def save(conf: dict) -> None:
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(conf, ensure_ascii=False, indent=2))
    CONF.chmod(0o600)


def request(path: str, body: dict | None = None) -> dict:
    conf = load()
    host = conf.get("host", "127.0.0.1")
    port = int(conf.get("port", 8090))
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"http://{host}:{port}{path}", data=data,
        headers={"Content-Type": "application/json",
                 "X-JKM-Token": conf.get("token", "")},
        method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        payload = e.read().decode()
        raise SystemExit(f"HTTP {e.code}: {payload}")


def show(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def pair() -> None:
    info = request("/api/pair/code")
    print(f"Код: {info['code']}  (живёт {info['expires_in']} с)")
    print("В приложении: меню → «Привязать компьютер» → ввести код.")
    url = info.get("url", "")
    qrencode = shutil.which("qrencode")
    if qrencode and url:
        try:
            subprocess.run([qrencode, "-t", "ANSIUTF8", url], check=True)
        except Exception:
            print("QR:", url)
    else:
        print("QR: установите qrencode или откройте", url)


def doctor() -> None:
    conf = load()
    print(f"адрес: http://{conf.get('host')}:{conf.get('port')}")
    try:
        s = request("/api/status")
        print("сервер:", s.get("version"), "| связь:", s["sensors"].get("connected"),
              "| режим:", s.get("mode"), "| анимация:", s.get("animation"))
        print("звук:", s.get("sound"))
    except SystemExit as e:
        print("сервер недоступен:", e)
    print("устройство: VID=%s PID=%s BAUD=%s TTY=%s" % (
        os.environ.get("JKM_VID", "1a86"), os.environ.get("JKM_PID", "5722"),
        os.environ.get("JKM_BAUD", "9600"), os.environ.get("JKM_TTY", "авто")))
    print("конфиг:", CONF, "есть" if CONF.exists() else "нет")


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        print(__doc__)
        return 0
    cmd, rest = args[0], args[1:]
    if cmd == "status":
        show(request("/api/status"))
    elif cmd == "sensors":
        show(request("/api/sensors"))
    elif cmd == "mode" and rest:
        key = rest[0].lower()
        show(request("/api/mode", {"mode": MODES.get(key, key)}))
    elif cmd == "anim" and rest:
        key = rest[0].lower()
        show(request("/api/animation", {"animation": ANIMS.get(key, key)}))
    elif cmd == "on":
        show(request("/api/display", {"on": True}))
    elif cmd == "off":
        show(request("/api/display", {"on": False}))
    elif cmd == "pair":
        pair()
    elif cmd == "devices":
        show(request("/api/pair/devices"))
    elif cmd == "revoke" and rest:
        show(request("/api/pair/revoke", {"token": rest[0]}))
    elif cmd == "config":
        conf = load()
        if rest == ["show"] or not rest:
            show({**conf, "token": ("есть" if conf.get("token") else "нет")})
        else:
            for item in rest:
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k in ("host", "port", "token"):
                        conf[k] = int(v) if k == "port" else v
            save(conf)
            show({**conf, "token": ("есть" if conf.get("token") else "нет")})
    elif cmd == "require-token" and rest:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "jkm_pairing", Path(__file__).resolve().parent.parent / "server" / "pairing.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        show(mod.set_config(require_token=rest[0]))
        print("перезапустите службу: sudo systemctl restart jkm-lcd")
    elif cmd == "doctor":
        doctor()
    elif cmd == "test":
        show(request("/api/raw", {"hex": "2a3240b004b80b1e0023000000", "seconds": 10}))
        print("10 секунд идёт тестовый кадр: цифры 42, шкала 50 %, без вкладки. Смотри на экран.")
    else:
        print("неизвестная команда:", cmd, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
