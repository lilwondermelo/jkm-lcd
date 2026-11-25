# Установка (Linux, любой дистрибутив)

Сервер — Python 3.10+ со стандартной библиотекой. Никаких pip-пакетов нет.
Для звуковых функций нужны `pactl`/`parec` из PulseAudio/PipeWire (клиентские
утилиты), для чтения мощности CPU (RAPL) — root.

## Из исходников

```bash
git clone https://github.com/GITHUB_USER/jkm-lcd.git
cd jkm-lcd
./bin/jkmctl config host=127.0.0.1 port=8090 show
sudo cp systemd/jkm-lcd.service /etc/systemd/system/jkm-lcd.service
sudo systemctl daemon-reload
sudo systemctl enable --now jkm-lcd
curl http://127.0.0.1:8090/api/health
```

## Что поправить под свою машину

1. `WorkingDirectory` и `ExecStart` в юните — пути к репозиторию.
2. `User=root` — нужен только для `/sys/class/powercap/intel-rapl:0/energy_uj`.
   Если RAPL недоступен, сервер просто не шлёт кадры (не показывает выдуманные
   ватты). Можно запускать от пользователя и убрать зависимость от RAPL.
3. `/dev/ttyACM*` — поиск по VID/PID 1a86:5722, жёсткий путь не нужен.
   Права на порт: пользователь должен быть в группе `dialout` (если не root).
4. Порт 8090 по умолчанию слушает `0.0.0.0`. Для LAN это нормально; наружу
   через nginx не публиковать. Для локального режима — `JKM_HOST=127.0.0.1`.
5. Звук: сервер подключается к первому найденному `/run/user/*/pulse/native`.
   На машине без PipeWire анимация «эквалайзер» будет показывать 0.
6. `systemd` есть не везде — на Alpine/OpenRC используйте свой unit/скрипт,
   команда `python3 -u server/main.py` та же.

## Arch (AUR)

`packaging/arch/PKGBUILD` — собрать и установить:

```bash
cd packaging/arch
makepkg -si
sudo systemctl enable --now jkm-lcd
```

## Другие дистрибутивы (npm)

`packaging/npm` содержит CLI-пакет: `npm i -g ./packaging/npm`, дальше
`jkmctl doctor`. Сам сервер остаётся Python-скриптом из репозитория.

## Проверка

```bash
jkmctl doctor
curl http://<host>:8090/api/status | python3 -m json.tool
jkmctl mode CPU && jkmctl anim eq
```
