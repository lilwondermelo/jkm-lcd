# JKM LCD — telecomando del display del dissipatore

[Русский](README.md) · [English](README_EN.md) · [Deutsch](README_DE.md) · [Español](README_ES.md) · [Français](README_FR.md) · [中文](README_ZH.md) · [日本語](README_JA.md) · [한국어](README_KO.md) · [Português](README_PT.md)

Telecomando leggero per il display a segmenti JKM (USB 1a86:5722, CDC-ACM, 9600 8N1):
server Python (solo libreria standard), PWA, app Android nativa «Kuler» e CLI `jkmctl`.

## Funzioni
- Cifre: temperatura CPU, temperatura GPU, orologio (HH/MM ogni 2 s), volume.
- Barra inferiore (indipendente dalle cifre): onda, ping-pong, respirazione,
  barra CPU, barra GPU (20–90 °C, lampeggia da 80 °C), barra del volume,
  equalizzatore (livello audio), vuoto.
- Indicatori superiori: sinistra = ore, destra = minuti, centro = temperatura/volume.
- Spegnimento chiude la porta seriale; accensione rifà l'handshake.
- Accoppiamento: codice a 4 cifre o QR; il telefono riceve un token una volta.

## Avvio rapido
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://<HOST>:8090/api/status
```
Apri `http://<IP-del-server>:8090`. Serve Linux, Python 3.10+ e
`pactl`/`parec` per l'audio; RAPL richiede root.

Готовый APK «Кулер»: [com.arch.kuler_18.apk](apk/com.arch.kuler_18.apk) (подпись release-ключом, `versionCode 18`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
Configurazione: `~/.config/jkm-lcd/config.json` (600).

## Accoppiamento
Esegui `jkmctl pair` sul server e inserisci il codice a 4 cifre nell'app.
Revoca con `jkmctl revoke <prefisso>`; rendi obbligatorio con `jkmctl require-token on`.

## API
`/api/status`, `/api/sensors`, `/api/mode`, `/api/animation`, `/api/display`,
`/api/pair/code`, `/api/pair`, `/api/pair/devices`, `/api/pair/revoke`, `/api/raw`.
Docs: [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/CLI.md](docs/CLI.md).

## Pacchetti
Arch: AUR [PKGBUILD](packaging/arch/PKGBUILD). Altre distro: [pacchetto npm](packaging/npm).
Uso personale.
