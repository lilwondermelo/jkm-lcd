# JKM LCD — control remoto de la pantalla

[Русский](README.md) · [English](README_EN.md) · [Deutsch](README_DE.md) · Français · 中文 · 日本語 · 한국어 · Português · Italiano

Pequeño control para la pantalla LCD de segmentos JKM (USB 1a86:5722, CDC-ACM, 9600 8N1):
servidor en Python (solo biblioteca estándar), PWA, app Android nativa «Kuler» y CLI `jkmctl`.

## Funciones
- Dígitos: temperatura CPU, temperatura GPU, reloj (HH/MM cada 2 s), volumen.
- Barra inferior (independiente de los dígitos): ola, ping-pong, respiración,
  barra de CPU, barra de GPU (20–90 °C, parpadeo desde 80 °C), barra de volumen,
  ecualizador (nivel de audio), vacío.
- Indicadores superiores: izquierda = horas, derecha = minutos, centro = temperatura/volumen.
- Apagar cierra el puerto serie; encender hace un nuevo handshake.
- Emparejamiento: código de 4 dígitos o QR; el teléfono recibe un token una vez.

## Inicio rápido
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://localhost:8090/api/status
```
Abre `http://<IP-del-cube>:8090`. Requiere Linux, Python 3.10+ y
`pactl`/`parec` para audio; RAPL necesita root.

Готовый APK «Кулер»: [com.arch.kuler_16.apk](apk/com.arch.kuler_16.apk) (подпись release-ключом, `versionCode 16`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
Configuración: `~/.config/jkm-lcd/config.json` (600).

## Emparejamiento
Ejecuta `jkmctl pair` en el equipo e introduce el código de 4 dígitos en la app.
Revoca tokens con `jkmctl revoke <prefijo>`; actívalos con `jkmctl require-token on`.

## API
`/api/status`, `/api/sensors`, `/api/mode`, `/api/animation`, `/api/display`,
`/api/pair/code`, `/api/pair`, `/api/pair/devices`, `/api/pair/revoke`, `/api/raw`.
Docs: [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/CLI.md](docs/CLI.md).

## Paquetes
Arch: AUR [PKGBUILD](packaging/arch/PKGBUILD). Otras distros: [paquete npm](packaging/npm).
Uso personal.
