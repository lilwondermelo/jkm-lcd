#!/usr/bin/env python3
"""Сопряжение телефона с кубом по четырёхзначному коду.

Никакого копирования токена: пульт на кубе показывает код на 5 минут,
телефон вводит его один раз и получает свой device-token, который хранится
в настройках приложения и уходит в заголовке X-JKM-Token.

Файлы (только права 600):
  ~/.local/state/jkm-lcd/pair.json   — текущий код и список устройств
  ~/.config/jkm-lcd/server.json      — host/port/require_token
"""
from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path

# Сервер systemd работает от root (RADL), поэтому не используем Path.home()
# напрямую: оба процесса должны видеть одни и те же файлы.
HOME = Path(os.environ.get("JKM_HOME",
                           "/home/Arch" if Path("/home/Arch").is_dir() else str(Path.home())))
STATE_FILE = Path(os.environ.get("JKM_PAIR_FILE",
                                 str(HOME / ".local/state/jkm-lcd/pair.json")))
CONF_FILE = Path(os.environ.get("JKM_CONF_FILE",
                                str(HOME / ".config/jkm-lcd/server.json")))
CODE_TTL = 300


def _read(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return dict(default)


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    try:
        path.chmod(0o600)
    except OSError:
        pass


def load_config() -> dict:
    conf = {"host": "0.0.0.0", "port": 8090, "require_token": False}
    conf.update(_read(CONF_FILE, {}))
    return conf


def set_config(**values) -> dict:
    conf = load_config()
    for key, value in values.items():
        if key == "require_token":
            conf[key] = str(value).lower() in ("1", "true", "yes", "on")
        elif key == "port":
            conf[key] = int(value)
        elif key in ("host",):
            conf[key] = str(value)
    _write(CONF_FILE, conf)
    return conf


def new_code() -> dict:
    data = _read(STATE_FILE, {"code": None, "expires": 0, "devices": []})
    code = f"{secrets.randbelow(10000):04d}"
    data["code"] = code
    data["expires"] = time.time() + CODE_TTL
    data.setdefault("devices", [])
    _write(STATE_FILE, data)
    return {"code": code, "expires_in": CODE_TTL}


def redeem(code: str, label: str = "") -> dict:
    data = _read(STATE_FILE, {"code": None, "expires": 0, "devices": []})
    if not data.get("code") or str(code).strip() != data["code"]:
        raise ValueError("неверный код")
    if time.time() > data.get("expires", 0):
        raise ValueError("код устарел — запроси новый")
    token = secrets.token_hex(24)
    devices = data.setdefault("devices", [])
    devices.append({"token": token, "label": label[:60], "paired_at": time.time()})
    data["code"] = None
    data["expires"] = 0
    _write(STATE_FILE, data)
    return {"token": token}


def verify(token: str) -> bool:
    data = _read(STATE_FILE, {"devices": []})
    return any(d.get("token") == token for d in data.get("devices", []))


def devices() -> list:
    data = _read(STATE_FILE, {"devices": []})
    return [{"label": d.get("label", ""),
             "paired_at": d.get("paired_at"),
             "token": (d.get("token") or "")[:8] + "…"} for d in data.get("devices", [])]


def revoke(prefix: str) -> int:
    data = _read(STATE_FILE, {"devices": []})
    before = len(data.get("devices", []))
    data["devices"] = [d for d in data.get("devices", [])
                       if not (d.get("token") or "").startswith(prefix)]
    _write(STATE_FILE, data)
    return before - len(data["devices"])
