# JKM LCD — cooler display remote

[Русский](README.md) · Deutsch · Español · Français · 中文 · 日本語 · 한국어 · Português · Italiano

A small remote for the JKM segment LCD (USB 1a86:5722, CDC-ACM, 9600 8N1):
Python stdlib server, PWA, native Android app «Kuler», and `jkmctl` CLI.

## Features
- Digits: CPU temp, GPU temp, clock (HH/MM every 2 s), volume.
- Bottom bar (independent of digits): wave snake, ping-pong, breathe,
  CPU temp bar, GPU temp bar (20–90 °C, blink at 80 °C), volume bar,
  equalizer (live audio level), empty.
- Top tabs: left = hours, right = minutes, center = temperature/volume.
- Power off closes the serial port; on reconnects with handshake.
- Pairing: 4-digit code or QR; the phone receives a device token once.

## Quick start
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://<HOST>:8090/api/status
```
Open `http://<cube-LAN-IP>:8090`. Needs Linux, Python 3.10+, and
`pactl`/`parec` for audio features. RAPL sensors require root.

Готовый APK «Кулер»: [com.arch.kuler_17.apk](apk/com.arch.kuler_17.apk) (подпись release-ключом, `versionCode 17`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
Config: `~/.config/jkm-lcd/config.json` (600).

## Pairing
Run `jkmctl pair` on the cube, enter the 4-digit code in the PWA/app.
Tokens can be revoked with `jkmctl revoke <prefix>`. Enable mandatory tokens
with `jkmctl require-token on`; <HOST> requests stay token-free.

## API
`/api/status`, `/api/sensors`, `/api/mode`, `/api/animation`, `/api/display`,
`/api/pair/code`, `/api/pair`, `/api/pair/devices`, `/api/pair/revoke`,
`/api/raw` (frame diagnostics). Full docs: [docs/PROTOCOL.md](docs/PROTOCOL.md),
[docs/CLI.md](docs/CLI.md), [docs/INSTALL.md](docs/INSTALL.md).

## Packaging
Arch: AUR [PKGBUILD](packaging/arch/PKGBUILD). Other distros: [npm package](packaging/npm).
Personal/home use license.
