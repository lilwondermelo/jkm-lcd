#!/usr/bin/env python3
"""Звук на кубе: громкость и уровень сигнала для анимации «Эквалайзер».

Сервер работает от root, а PipeWire — в сессии пользователя, поэтому
подключаемся к его сокету PulseAudio через PULSE_SERVER.

  * volume() — текущая громкость основного выхода, 0..100;
  * Level — фоновый поток: читает монитор выхода и считает RMS. Считаем,
    что звук идёт, только когда уровень выше порога тишины — так надёжнее,
    чем смотреть на список потоков (у PipeWire нет State: RUNNING, а
    «лишние» потоки вроде браузера висят постоянно).
"""
from __future__ import annotations

import array
import glob
import math
import os
import re
import subprocess
import threading

_PULSE_CANDIDATES = sorted(glob.glob("/run/user/*/pulse/native"))
SILENCE_RMS = 40       # ниже — тишина
CHUNK_MS = 30          # ~33 замера в секунду
BEAT_FACTOR = 1.15     # всплеск выше среднего — удар
SENSITIVITY = 260.0    # громче отклик на тихую музыку


def _env() -> dict:
    env = os.environ.copy()
    if _PULSE_CANDIDATES:
        env.setdefault("PULSE_SERVER", "unix:" + _PULSE_CANDIDATES[0])
    return env


def _run(cmd: list[str], timeout: float = 2.0) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             env=_env())
        return out.stdout or ""
    except Exception:
        return ""


def volume() -> int | None:
    out = _run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"])
    m = re.search(r"(\d+)%", out)
    return int(m.group(1)) if m else None


class Level(threading.Thread):
    """Постоянно читает монитор выхода, держит уровень 0..100 и флаг активности."""

    def __init__(self):
        super().__init__(daemon=True)
        self.value = 0
        self.active = False
        self.beat = False
        self._stop = threading.Event()

    def run(self):
        while not self._stop.is_set():
            try:
                proc = subprocess.Popen(
                    ["parec", "--raw", "--latency-msec=15",
                     "-d", "@DEFAULT_MONITOR@",
                     "--rate=8000", "--channels=1", "--format=s16le"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=_env())
            except Exception:
                threading.Event().wait(0.5)
                continue
            try:
                while not self._stop.is_set():
                    chunk = proc.stdout.read(480)  # 30 мс при 8 кГц / 16 бит
                    if not chunk:
                        break
                    a = array.array("h")
                    a.frombytes(chunk[: len(chunk) // 2 * 2])
                    if not a:
                        continue
                    rms = math.sqrt(sum(x * x for x in a) / len(a))

                    # Медленное среднее — чтобы удар определить относительно
                    # текущей громкости, а не абсолютного порога.
                    avg = getattr(self, "_avg", rms)
                    avg = avg * 0.9 + rms * 0.1
                    self._avg = avg
                    beat = rms > 4000 and rms > avg * BEAT_FACTOR

                    # Масштаб относительно текущей громкости музыки: ровный
                    # звук держит шкалу около 70, удар добавляет всплеск до 100.
                    base = max(SENSITIVITY, avg)
                    target = min(100, int(rms / base * 80))
                    if beat:
                        target = 100
                    if rms < SILENCE_RMS:
                        target = 0
                    if target > self.value:
                        self.value = target
                    else:
                        self.value = max(target, int(self.value * 0.72))
                    self.beat = beat
                    self.active = self.value > 0
            finally:
                try:
                    proc.terminate()
                except Exception:
                    pass
                self.value = 0
                self.active = False
            threading.Event().wait(0.3)

    def stop(self):
        self._stop.set()
