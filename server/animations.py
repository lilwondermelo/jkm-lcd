#!/usr/bin/env python3
"""Modes and animations for the JKM segment display.

Железо: цифровое поле (температура) + шкала нагрузки 0..100. Шкала всегда
заполняется **слева направо** — направление зашито в прошивке, развернуть
его нельзя. Поэтому «справа налево» сделано как обратный ход: шкала
заполняется слева вправо, а гаснет справа налево (анимация pingpong).

Режимы (решение владельца #850/#856):
  * temp — температура CPU;
  * gpu  — температура GPU (0, если датчика нет).
Мощность убрана.

Анимации:
  * wave     — змейка слева вправо, добежала до края и начинает заново;
  * pingpong — заполняется вправо, гаснет справа налево (обратный ход);
  * breathe  — пульс: вся панель горит/гаснет одновременно;
  * thermo   — шкала = температура выбранного датчика, мигает при >= 80 °C;
  * eq       — шкала = уровень звука (из PipeWire), работает в любом режиме;
  * none     — «пусто»: шкала погашена (в часах — прогресс минуты).
"""
from __future__ import annotations

import time

MODES = ["temp", "gpu", "clock", "volume"]
ANIMATIONS = ["wave", "pingpong", "breathe", "cputemp",
              "gputemp", "volume", "eq", "none"]

# Волна-змейка: 10 сегментов по 10% — ступеньки видно, это «змейка».
WAVE_STEPS = 10
WAVE_STEP_SECONDS = 0.2
WAVE_HOLD_SECONDS = 0.15
WAVE_GAP_SECONDS = 0.35
WAVE_PERIOD = (WAVE_STEPS * WAVE_STEP_SECONDS
               + WAVE_HOLD_SECONDS + WAVE_GAP_SECONDS)

# Пинг-понг: вправо по сегменту, пауза, обратно влево, пауза.
PINGPONG_STEP_SECONDS = 0.18
PINGPONG_HOLD_SECONDS = 0.15
PINGPONG_GAP_SECONDS = 0.3
PINGPONG_PERIOD = (2 * WAVE_STEPS * PINGPONG_STEP_SECONDS
                   + 2 * PINGPONG_HOLD_SECONDS + PINGPONG_GAP_SECONDS)

# Дыхание-пульс: вся панель одновременно горит/гаснет.
BREATHE_ON_SECONDS = 1.4
BREATHE_OFF_SECONDS = 0.9
BREATHE_PERIOD = BREATHE_ON_SECONDS + BREATHE_OFF_SECONDS

# Термометр: 10 °C на сегмент, тревога с 80 °C (мигание).
TEMP_MIN_C = 20
TEMP_MAX_C = 90
THERMO_ALERT_C = 80

ANIMATION_PARAMS = {
    "wave": {
        "steps": WAVE_STEPS,
        "step_seconds": WAVE_STEP_SECONDS,
        "hold_seconds": WAVE_HOLD_SECONDS,
        "gap_seconds": WAVE_GAP_SECONDS,
        "period": round(WAVE_PERIOD, 3),
    },
    "pingpong": {
        "steps": WAVE_STEPS,
        "step_seconds": PINGPONG_STEP_SECONDS,
        "hold_seconds": PINGPONG_HOLD_SECONDS,
        "gap_seconds": PINGPONG_GAP_SECONDS,
        "period": round(PINGPONG_PERIOD, 3),
    },
    "breathe": {
        "on_seconds": BREATHE_ON_SECONDS,
        "off_seconds": BREATHE_OFF_SECONDS,
        "period": round(BREATHE_PERIOD, 3),
    },
    "cputemp": {
        "min_c": TEMP_MIN_C,
        "max_c": TEMP_MAX_C,
        "alert_c": THERMO_ALERT_C,
        "alert_period": 1.6,
    },
    "gputemp": {
        "min_c": TEMP_MIN_C,
        "max_c": TEMP_MAX_C,
        "alert_c": THERMO_ALERT_C,
        "alert_period": 1.6,
    },
    "eq": {
        "source": "pipewire-monitor",
        "chunk_ms": 50,
        "beat_factor": 1.22,
        "idle": 0,
    },
}


# Часы: большое поле вмещает 3 цифры, поэтому часы и минуты чередуются
# (2 с на каждое). Полное HHMM уходит в 4-значное поле частоты, а шкала
# показывает прогресс минуты.
CLOCK_FRAME_SECONDS = 2.0


def clock_parts(t: float) -> tuple[int, int]:
    now = time.localtime()
    return now.tm_hour, now.tm_min


def central_for_mode(mode: str, t: float, s: dict) -> tuple[int, int]:
    """Return (flags, central_value).

    flags 0x80 зажигает левую вкладку, 0x40 — правую; ttype != 0 — центральную.
    В режиме часов вкладка показывает, что именно сейчас на экране:
    часы (левая) или минуты (правая).
    """
    if mode == "gpu":
        return 0x40, int(s.get("gpu") or 0)
    if mode == "clock":
        hh, mm = clock_parts(t)
        if (t % (2 * CLOCK_FRAME_SECONDS)) < CLOCK_FRAME_SECONDS:
            return 0x80, hh
        return 0x40, mm
    if mode == "volume":
        return 0x40, int(s.get("volume") or 0)
    return 0x40, int(s["temp"] or 0)


def wave_load(t: float) -> int:
    """Шкала 0..100 ступеньками слева направо, затем пауза на нуле."""
    phase = t % WAVE_PERIOD
    fill = WAVE_STEPS * WAVE_STEP_SECONDS
    if phase >= fill + WAVE_HOLD_SECONDS:
        return 0
    if phase >= fill:
        return 100
    step = int(phase / WAVE_STEP_SECONDS) + 1
    return max(10, min(100, step * (100 // WAVE_STEPS)))


def pingpong_load(t: float) -> int:
    """Заполнение слева направо, затем гашение справа налево."""
    phase = t % PINGPONG_PERIOD
    up = WAVE_STEPS * PINGPONG_STEP_SECONDS
    if phase < up:
        step = int(phase / PINGPONG_STEP_SECONDS) + 1
        return max(10, min(100, step * (100 // WAVE_STEPS)))
    phase -= up
    if phase < PINGPONG_HOLD_SECONDS:
        return 100
    phase -= PINGPONG_HOLD_SECONDS
    if phase < up:
        # Обратный ход: шкала убывает — сегменты гаснут справа налево.
        left = WAVE_STEPS - int(phase / PINGPONG_STEP_SECONDS)
        return max(0, min(90, left * (100 // WAVE_STEPS)))
    phase -= up
    if phase < PINGPONG_HOLD_SECONDS:
        return 0
    return 0


def breathe_on(t: float) -> bool:
    """True — панель горит, False — все сегменты выключены (пульс)."""
    return (t % BREATHE_PERIOD) < BREATHE_ON_SECONDS


def sensor_temp(mode: str, s: dict) -> float | None:
    """Температура того датчика, который выбран в режиме (для термометра)."""
    if mode == "gpu":
        return s.get("gpu")
    return s.get("temp")


def temp_bar(temp: float | None) -> int:
    """Температура → шкала: 20 °C — пусто, 90 °C — полная, 7 °C на сегмент."""
    if temp is None:
        return 0
    return max(0, min(100, int(round(
        (temp - TEMP_MIN_C) / (TEMP_MAX_C - TEMP_MIN_C) * 100))))


def temp_bar_alert(t: float, temp: float | None) -> int:
    """Полоска температуры 20–90 °C; при ≥ 80 °C мигает."""
    load = temp_bar(temp)
    if temp is not None and temp >= THERMO_ALERT_C and (t % 1.6) >= 0.8:
        return 0
    return load


def render(mode: str, animation: str, t: float, s: dict) -> dict:
    """Build display values for one 13-byte frame.

    ``blackout`` просит отправить нулевой кадр: прошивка понимает нули как
    «нет данных» и гасит все сегменты (пульс «дыхание»).
    """
    flags, central = central_for_mode(mode, t, s)
    load = int(s["load"])
    clk_field = max(1, int(s["clock"]))
    if mode == "clock":
        hh, mm = clock_parts(t)
        clk_field = max(1, hh * 100 + mm)
        if animation == "none":
            load = int(round(mm / 59 * 100))
    if animation == "wave":
        load = wave_load(t)
    elif animation == "pingpong":
        load = pingpong_load(t)
    elif animation == "breathe":
        load = 100 if breathe_on(t) else 0
    elif animation == "cputemp":
        load = temp_bar_alert(t, s.get("temp"))
    elif animation == "gputemp":
        load = temp_bar_alert(t, s.get("gpu"))
    elif animation == "volume":
        load = int(s.get("volume") or 0)
    elif animation == "eq":
        load = int(s.get("level") or 0)  # уровень сигнала, в тишине — 0
    if animation == "none" and mode != "clock":
        load = 0  # «пусто» — нижний индикатор погашен

    # Центральное поле всегда показывает выбранное значение; при flags 0x80
    # продублируем его и в поле мощности, чтобы цифры не «прыгали».
    temp_field = central
    pwr_field = central if flags == 0x80 else max(1, int(round(s["power"] or 0)))

    blackout = animation == "breathe" and not breathe_on(t)
    # Верхние вкладки: 0 — °C/температура (правая), 1 — «не температура»
    # (центральная, у вендора это °F). Левая загорается при flags 0x80.
    # ttype != 0 зажигает центральную вкладку. Часы/звук — центр,
    # температура — тоже центр (по просьбе владельца), за исключением
    # часов: там вкладка показывает ЧЧ или ММ через flags.
    # Центр-вкладка (tempType != 0) временно отключена: есть подозрение,
    # что прошивка гаснет от ненулевого tempType. Вернём после теста.
    ttype = 0
    return {
        "temp": 0 if blackout else temp_field,
        "pwr": 0 if blackout else pwr_field,
        "clk": 0 if blackout else clk_field,
        "load": 0 if blackout else max(0, min(100, load)),
        "flags": flags,
        "ttype": ttype,
        "blackout": blackout,
    }
