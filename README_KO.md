# JKM LCD — CPU 쿨러 디스플레이 리모컨

[Русский](README.md) · [English](README_EN.md) · [Deutsch](README_DE.md) · [Español](README_ES.md) · [Français](README_FR.md) · [中文](README_ZH.md) · [日本語](README_JA.md) · Português · Italiano

JKM 세그먼트 LCD(USB 1a86:5722, CDC-ACM, 9600 8N1)용 경량 리모컨입니다.
Python 표준 라이브러리 서버, PWA, 네이티브 Android 앱 «Kuler», `jkmctl` CLI 포함.

## 기능
- 숫자 부분: CPU 온도, GPU 온도, 시계(시/분 2초마다 전환), 볼륨.
- 하단 바(숫자와 독립): 웨이브, 핑퐁, 브리딩, CPU 온도 바, GPU 온도 바
  (20–90 °C, 80 °C 이상에서 점멸), 볼륨 바, 이퀄라이저, 끄기.
- 상단 표시: 왼쪽=시, 오른쪽=분, 가운데=온도/볼륨.
- 전원 끄기는 시리얼 포트를 닫고, 켜기는 다시 핸드셰이크합니다.
- 페어링: 4자리 코드 또는 QR; 전화기는 토큰을 한 번만 받습니다.

## 빠른 시작
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://<HOST>:8090/api/status
```
`http://<서버IP>:8090` 접속. Linux, Python 3.10+, 오디오 기능은
`pactl`/`parec` 필요, RAPL은 root 권한 필요.

Готовый APK «Кулер»: [com.arch.kuler_18.apk](apk/com.arch.kuler_18.apk) (подпись release-ключом, `versionCode 18`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
설정: `~/.config/jkm-lcd/config.json` (600).

## 페어링
서버에서 `jkmctl pair` 실행 후 앱에 4자리 코드 입력.
`jkmctl revoke <접두사>`로 폐기, `jkmctl require-token on`으로 토큰 필수화
(로컬 요청은 예외).

## API
`/api/status`, `/api/sensors`, `/api/mode`, `/api/animation`, `/api/display`,
`/api/pair/code`, `/api/pair`, `/api/pair/devices`, `/api/pair/revoke`, `/api/raw`.
문서: [docs/PROTOCOL.md](docs/PROTOCOL.md), [docs/CLI.md](docs/CLI.md).

## 패키지
Arch: AUR [PKGBUILD](packaging/arch/PKGBUILD). 기타 배포판: [npm 패키지](packaging/npm).
개인 사용용.
