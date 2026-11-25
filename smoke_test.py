#!/usr/bin/env python3
"""Reproducible hardware smoke test for the JKM cooler LCD (1a86:5722).

    sudo python3 smoke_test.py [--seconds 5]

Checks, against the real device:
  * port discovery by USB VID/PID (not a hardcoded tty name);
  * three handshakes, each verified by the timestamp echo in bytes 12..15;
  * real coretemp and RAPL readings (RAPL is root-only);
  * a run of alternating 13/7-byte frames with no write errors.

Exit code 0 means PASS. The running jkm-lcd service is stopped for the
duration and started again afterwards (disable with --no-service-control).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import display, sensors  # noqa: E402

SERVICE = "jkm-lcd"


def service_active() -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "--quiet", SERVICE],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def service(action: str) -> None:
    subprocess.run(["systemctl", action, SERVICE], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fail(msg: str) -> int:
    print("FAIL:", msg)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=5.0,
                    help="frame run duration (default 5)")
    ap.add_argument("--no-service-control", action="store_true",
                    help="do not stop/start the jkm-lcd service")
    args = ap.parse_args()

    stopped = False
    if not args.no_service_control and service_active():
        print(f"stopping {SERVICE} for the test ...")
        service("stop")
        stopped = True
        time.sleep(0.5)

    d = None
    try:
        d = display.JkmDisplay()
        port = display.find_port()
        if not port:
            return fail("USB device 1a86:5722 not found")
        print("port:", port)
        if not d.connect():
            return fail("connect/handshake with the device failed")

        checks = 1  # connect() already performed one verified handshake
        for i in range(3):
            if not d.handshake():
                return fail(f"handshake {i + 2}: bad or missing timestamp echo")
            checks += 1
        print(f"handshake: {checks}/{checks} with valid timestamp echo")

        sens = sensors.Sensors()
        snap = sens.snapshot()
        deadline = time.time() + 3.0
        while (snap["temp"] is None or snap["power"] is None) and time.time() < deadline:
            time.sleep(0.2)
            snap = sens.snapshot()
        if snap["temp"] is None:
            return fail("coretemp sensor not found")
        if snap["power"] is None:
            return fail("RAPL power not readable (run as root)")
        print(f"sensors: temp={snap['temp']}C power={snap['power']}W "
              f"load={snap['load']}% clock={snap['clock']}MHz")

        # Prime a real frame set, no placeholder wattage.
        end = time.time() + args.seconds
        frames = 0
        while time.time() < end:
            snap = sens.snapshot()
            if snap["temp"] is None or snap["power"] is None:
                return fail("sensor data disappeared mid-run")
            pwr = max(1, int(round(snap["power"])))
            if not d.send(snap["temp"], snap["load"], 0x40,
                          display.RPM_PLACEHOLDER, max(1, snap["clock"]),
                          pwr, snap["gpu"], 0):
                return fail(f"frame write failed after {frames} frames")
            frames += 1
            time.sleep(0.1)
        print(f"frames: {frames} sent in {args.seconds:.1f}s, no errors")
        print("PASS")
        return 0
    finally:
        if d is not None:
            d.close()
        if stopped:
            print(f"starting {SERVICE} ...")
            service("start")


if __name__ == "__main__":
    sys.exit(main())
