# JKM LCD — 冷却器液晶画面的遥控器

[Русский](README.md) · [English](README_EN.md) · [Deutsch](README_DE.md) · [Español](README_ES.md) · [Français](README_FR.md) · [中文](README_ZH.md) · 한국어 · Português · Italiano

JKM セグメント LCD（USB 1a86:5722、CDC-ACM、9600 8N1）用の軽量遥控器です。
Python 標準ライブラリのサーバー、PWA、Android ネイティブアプリ「Kuler」、
`jkmctl` CLI を含みます。

## 機能
- 数字部：CPU 温度、GPU 温度、時計（時/分を 2 秒ごと）、音量。
- 下部バー（数字とは独立）：ウェーブ、ピンポン、ブリージング、CPU 温度バー、
  GPU 温度バー（20–90 °C、80 °C 以上で点滅）、音量バー、イコライザー、消灯。
- 上部インジケーター：左=時、右=分、中央=温度/音量。
- オフでシリアルポートを閉じ、オンで再ハンドシェイク。
- ペアリング：4 桁コードまたは QR。端末はトークンを一度だけ受け取ります。

## クイックスタート
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://<HOST>:8090/api/status
```
`http://<サーバーIP>:8090` を開きます。Linux、Python 3.10+、音声機能には
`pactl`/`parec` が必要です。RAPL は root 権限が必要です。

Готовый APK «Кулер»: [com.arch.kuler_19.apk](apk/com.arch.kuler_19.apk) (подпись release-ключом, `versionCode 19`).

Релиз GitHub: https://github.com/lilwondermelo/jkm-lcd/releases/tag/v3.0.1 (APK также в ассетах).

> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.

## CLI
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
設定：`~/.config/jkm-lcd/config.json` (600)。

## ペアリング
サーバーで `jkmctl pair` を実行し、アプリに 4 桁コードを入力。
`jkmctl revoke <接頭辞>` で失効、`jkmctl require-token on` でトークン必須化
（ローカルは例外）。

## API
`/api/status`、`/api/sensors`、`/api/mode`、`/api/animation`、`/api/display`、
`/api/pair/code`、`/api/pair`、`/api/pair/devices`、`/api/pair/revoke`、`/api/raw`。
詳細：[docs/PROTOCOL.md](docs/PROTOCOL.md)、[docs/CLI.md](docs/CLI.md)。

## パッケージ
Arch：AUR [PKGBUILD](packaging/arch/PKGBUILD)。その他：[npm パッケージ](packaging/npm)。
個人利用向け。
