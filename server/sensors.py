#!/usr/bin/env python3
"""Sensor readers for the JKM LCD project (Linux, root for RAPL)."""
from __future__ import annotations

import glob
import os
import re
import subprocess
import time

RAPL = "/sys/class/powercap/intel-rapl:0/energy_uj"
RAPL_MAX = "/sys/class/powercap/intel-rapl:0/max_energy_range_uj"


def read_temp() -> int | None:
    """CPU package temperature, or None when no coretemp sensor is present."""
    for hw in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            if open(os.path.join(hw, "name")).read().strip() == "coretemp":
                return int(open(os.path.join(hw, "temp1_input")).read()) // 1000
        except OSError:
            pass
    return None


def read_clock() -> int:
    try:
        khz = int(open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq").read())
        return max(1, khz // 1000)
    except OSError:
        pass
    try:
        m = re.search(r"cpu MHz\s*:\s*([0-9.]+)", open("/proc/cpuinfo").read())
        if m:
            return max(1, int(float(m.group(1))))
    except OSError:
        pass
    return 0


_gpu = (0.0, 0)


def read_gpu() -> int:
    global _gpu
    now = time.time()
    if now - _gpu[0] < 5:
        return _gpu[1]
    val = 0
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL, timeout=2, text=True)
        val = int(out.strip().splitlines()[0])
    except Exception:
        val = 0
    _gpu = (now, val)
    return val


class Rapl:
    def __init__(self):
        self.last = None
        self.last_t = None
        # No placeholder wattage: until two samples exist the value is None
        # and the display loop waits instead of showing a fake 30 W.
        self.value = None
        try:
            self.max = int(open(RAPL_MAX).read())
        except OSError:
            self.max = 0

    def watts(self) -> float | None:
        try:
            now = int(open(RAPL).read())
        except OSError:
            return None
        t = time.monotonic()
        prev, prev_t = self.last, self.last_t
        self.last, self.last_t = now, t
        if prev is None or prev_t is None:
            return None
        d = now - prev
        if d < 0 and self.max:
            d += self.max
        dt = t - prev_t
        if dt <= 0:
            return self.value
        self.value = max(1.0, d / 1e6 / dt)
        return self.value


class Load:
    def __init__(self):
        self.prev = self._read()

    @staticmethod
    def _read():
        vals = [int(x) for x in open("/proc/stat").readline().split()[1:]]
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        return sum(vals), idle

    def percent(self) -> int:
        total, idle = self._read()
        dt = total - self.prev[0]
        di = idle - self.prev[1]
        self.prev = (total, idle)
        if dt <= 0:
            return 0
        return max(0, min(100, int(100 * (1 - di / dt))))


class Sensors:
    def __init__(self):
        self.rapl = Rapl()
        self.load = Load()

    def snapshot(self) -> dict:
        pwr = self.rapl.watts()
        return {
            "temp": read_temp(),
            "power": round(pwr, 1) if pwr is not None else None,
            "load": self.load.percent(),
            "clock": read_clock(),
            "gpu": read_gpu(),
        }
