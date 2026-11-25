#!/usr/bin/env python3
"""JKM LCD serial protocol (Turing-like rev-D variant, 1a86:5722)."""
from __future__ import annotations

import glob
import os
import select
import struct
import termios
import time

VID, PID = "1a86", "5722"
BAUD = termios.B9600
# The firmware treats a zero RPM field as "no data" and blanks the screen.
# This cooler has no tach line, so a placeholder is required.
RPM_PLACEHOLDER = 1200


def find_port():
    for p in glob.glob("/dev/ttyACM*"):
        name = os.path.basename(p)
        d = os.path.realpath(f"/sys/class/tty/{name}/device")
        for _ in range(8):
            vf = os.path.join(d, "idVendor")
            pf = os.path.join(d, "idProduct")
            if os.path.exists(vf) and os.path.exists(pf):
                try:
                    if open(vf).read().strip() == VID and open(pf).read().strip() == PID:
                        return p
                except OSError:
                    pass
                break
            d = os.path.dirname(d)
    return None


class JkmDisplay:
    def __init__(self):
        self.fd = None
        self.path = None

    def _open(self, path: str):
        fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        a = termios.tcgetattr(fd)
        a[0] = 0
        a[1] = 0
        a[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        a[3] = 0
        a[4] = BAUD
        a[5] = BAUD
        a[6][termios.VMIN] = 0
        a[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, a)
        termios.tcflush(fd, termios.TCIOFLUSH)
        return fd

    def _read_n(self, n: int, timeout: float = 0.6) -> bytes:
        assert self.fd is not None
        buf = b""
        end = time.time() + timeout
        while len(buf) < n and time.time() < end:
            r, _, _ = select.select([self.fd], [], [], 0.1)
            if r:
                try:
                    chunk = os.read(self.fd, n - len(buf))
                except OSError:
                    break
                if chunk:
                    buf += chunk
        return buf

    def handshake(self) -> bool:
        """Send low32(.NET ticks) and verify the device echoes it back.

        The 16-byte reply carries the sent timestamp in bytes 12..15
        (little-endian); bytes 0..11 are ``Signal XOR timestamp``.
        A reply of the right length but with a different tail is a failure.
        """
        if self.fd is None:
            return False
        # Drop any queued replies (e.g. command echoes) so the 16-byte
        # handshake reply is read from a clean stream.
        try:
            termios.tcflush(self.fd, termios.TCIFLUSH)
        except (OSError, termios.error):
            self.close()
            return False
        ticks = int(time.time() * 10_000_000) + 621355968000000000
        payload = struct.pack("<I", ticks & 0xFFFFFFFF)
        try:
            os.write(self.fd, payload)
        except OSError:
            self.close()
            return False
        time.sleep(0.25)
        resp = self._read_n(16, 0.8)
        return len(resp) == 16 and resp[12:16] == payload

    def connect(self) -> bool:
        self.close()
        path = find_port()
        if not path:
            return False
        try:
            self.fd = self._open(path)
        except OSError:
            self.fd = None
            return False
        self.path = path
        if not self.handshake():
            self.close()
            return False
        return True

    def close(self):
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
        self.fd = None
        self.path = None

    def send_bytes(self, data: bytes) -> bool:
        """Отправить произвольные байты (диагностика протокола)."""
        if self.fd is None:
            return False
        try:
            os.write(self.fd, data)
        except OSError:
            self.close()
            return False
        return True

    def send(self, temp: int, load: int, flags: int, rpm: int, clk: int,
             pwr: int, gpu: int, ttype: int = 0) -> bool:
        if self.fd is None:
            return False
        # Vendor FanCondrol always writes full 13-byte frames (its
        # data_send_flag length is overwritten with 13), so do the same.
        f = bytes([
            temp & 0xFF, load & 0xFF, flags & 0xFF,
            rpm & 0xFF, (rpm >> 8) & 0xFF,
            clk & 0xFF, (clk >> 8) & 0xFF,
            pwr & 0xFF, (pwr >> 8) & 0xFF,
            gpu & 0xFF, 0, ttype & 0xFF, 0,
        ])
        try:
            os.write(self.fd, f)
        except OSError:
            self.close()
            return False
        r, _, _ = select.select([self.fd], [], [], 0)
        if r:
            try:
                os.read(self.fd, 4096)
            except OSError:
                pass
        return True
