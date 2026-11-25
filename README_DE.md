# JKM LCD — Fernbedienung für das Kühler-Display

[Русский](README.md) · [English](README_EN.md) · Español · Français · 中文 · 日本語 · 한국어 · Português · Italiano

Kleine Steuerung für das JKM-Segment-LCD (USB 1a86:5722, CDC-ACM, 9600 8N1):
Python-Server (Standardbibliothek), PWA, native Android-App «Kuler» und `jkmctl`.

## Funktionen
- Ziffern: CPU-Temperatur, GPU-Temperatur, Uhr (HH/MM alle 2 s), Lautstärke.
- Untere Skala (unabhängig von den Ziffern): Welle, Ping-Pong, Atmen,
  CPU-Skala, GPU-Skala (20–90 °C, Blinken ab 80 °C), Lautstärke-Skala,
  Equalizer (Audio-Pegel), leer.
- Obere Anzeigen: links = Stunden, rechts = Minuten, Mitte = Temperatur/Lautstärke.
- Ausschalten schließt den Serial-Port, Einschalten macht erneut Handshake.
- Kopplung: 4-stelliger Code oder QR; das Telefon erhält einmalig ein Token.

## Schnellstart
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://localhost:8090/api/status
```
Danach `http://<IP-des-Cube>:8090` öffnen. Linux, Python 3.10+ und
`pactl`/`parec` für Audio nötig; RAPL braucht root.

Готовый APK «Кулер»: [com.arch.kuler_16.apk](apk/com.arch.kuler_16.apk) (подпись release-ключом, `versionCode 16`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
Konfiguration: `~/.config/jkm-lcd/config.json` (600).

## Kopplung
`jkmctl pair` auf dem Cube ausführen, 4-stelligen Code in der App eingeben.
Tokens mit `jkmctl revoke <prefix>` widerrufen; mit `jkmctl require-token on`
obligatorisch machen (localhost bleibt ohne Token).

## API
`/api/status`, `/api/sensors`, `/api/mode`, `/api/animation`, `/api/display`,
`/api/pair/code`, `/api/pair`, `/api/pair/devices`, `/api/pair/revoke`, `/api/raw`.
Dokumentation: [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/CLI.md](docs/CLI.md).

## Pakete
Arch: AUR [PKGBUILD](packaging/arch/PKGBUILD). Andere Distributionen: [npm-Paket](packaging/npm).
Nur für den privaten Gebrauch.
