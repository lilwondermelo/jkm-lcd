# JKM LCD — 风扇屏幕遥控器

[Русский](README.md) · [English](README_EN.md) · [Deutsch](README_DE.md) · [Español](README_ES.md) · [Français](README_FR.md) · 日本語 · 한국어 · Português · Italiano

用于 JKM 段码屏（USB 1a86:5722，CDC-ACM，9600 8N1）的轻量遥控器：
Python 标准库服务器、PWA、原生 Android 应用「Cooler」以及 `jkmctl` 命令行工具。

## 功能
- 数字区：CPU 温度、GPU 温度、时钟（时/分每 2 秒切换）、音量。
- 下方十段条（与数字独立）：波浪蛇形、往返、呼吸、CPU 温度条、
  GPU 温度条（20–90 °C，80 °C 起闪烁）、音量条、均衡器（实时音频电平）、空白。
- 上方三个指示位：左=小时，右=分钟，中间=温度/音量。
- 关屏会关闭串口；开屏时重新握手。
- 配对：4 位数字码或二维码；手机只获取一次设备令牌。

## 快速开始
```bash
git clone https://github.com/lilwondermelo/jkm-lcd.git
cd jkm-lcd
sudo cp systemd/jkm-lcd.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now jkm-lcd
curl http://localhost:8090/api/status
```
然后打开 `http://<主机IP>:8090`。需要 Linux、Python 3.10+，音频功能需要
`pactl`/`parec`；RAPL 需要 root 权限。

## 命令行
`jkmctl status | mode CPU|GPU|clock|volume | anim wave|cpu|gpu|volume|eq | on | off | pair | devices | doctor`
配置：`~/.config/jkm-lcd/config.json` (600)。

## 配对
在电脑上运行 `jkmctl pair`，在应用中输入 4 位码。
用 `jkmctl revoke <前缀>` 撤销；`jkmctl require-token on` 开启强制令牌
（本机请求仍无需令牌）。

## API
`/api/status`、`/api/sensors`、`/api/mode`、`/api/animation`、`/api/display`、
`/api/pair/code`、`/api/pair`、`/api/pair/devices`、`/api/pair/revoke`、`/api/raw`。
文档：[docs/PROTOCOL.md](docs/PROTOCOL.md)、[docs/CLI.md](docs/CLI.md)。

## 软件包
Arch：AUR [PKGBUILD](packaging/arch/PKGBUILD)。其他发行版：[npm 包](packaging/npm)。
仅限个人使用。
