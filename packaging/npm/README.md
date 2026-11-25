# @arch-home/jkm-lcd

CLI `jkmctl` для пульта JKM LCD на любом Linux-дистрибутиве. Сам сервер —
Python stdlib (`server/main.py`),входит в этом пакете.

```bash
npm i -g @arch-home/jkm-lcd
jkmctl doctor
jkmctl pair
jkmctl mode CPU
jkmctl anim eq
```

Пакет не хранит секреты: настройки — `~/.config/jkm-lcd/config.json` (600),
сопряжение — `~/.local/state/jkm-lcd/pair.json` (600).
