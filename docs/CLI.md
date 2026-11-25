# CLI — jkmctl

Управление пультом с компьютера. Скрипт на Python stdlib: `bin/jkmctl` (можно
установить в `~/.local/bin/jkmctl`).

## Команды

| Команда | Что делает |
|---|---|
| `jkmctl status` | версия, режим, анимация, вкладка, датчики, звук |
| `jkmctl sensors` | только датчики |
| `jkmctl mode CPU\|GPU\|Часы\|Громкость` | цифровое поле |
| `jkmctl anim волна\|пинг-понг\|дыхание\|cpu\|gpu\|volume\|eq\|пусто` | нижняя шкала |
| `jkmctl on` / `jkmctl off` | питание экрана |
| `jkmctl pair` | 4-значный код + QR (нужен `qrencode`) |
| `jkmctl devices` | список привязанных устройств |
| `jkmctl revoke <префикс>` | отозвать устройство |
| `jkmctl require-token on\|off` | обязательный токен для удалённых запросов |
| `jkmctl config host=… port=… token=… show` | настройки CLI |
| `jkmctl doctor` | быстрая диагностика |

Для `mode`/`anim` принимаются и английские, и русские имена; старый режим
`sound` автоматически превращается в `volume`.

## Настройки

- `~/.config/jkm-lcd/config.json` (600) — CLI: `host`, `port`, `token`.
- `~/.config/jkm-lcd/server.json` (600) — сервер: `host`, `port`, `require_token`.
- `~/.local/state/jkm-lcd/pair.json` (600) — код и список устройств.

Переменные окружения сервера: `JKM_HOST`, `JKM_PORT`, `JKM_REQUIRE_TOKEN`,
`JKM_PAIR_FILE`, `JKM_CONF_FILE`, `JKM_STATE_FILE`.

## Сопряжение

```bash
jkmctl pair       # код на 5 минут, QR со ссылкой
# в PWA/приложении: «привязать» → 4 цифры → сохранить токен
jkmctl devices
jkmctl require-token on && sudo systemctl restart jkm-lcd
```

После включения `require-token` локальные запросы с 127.0.0.1 работают без
токена; удалённые требуют заголовок `X-JKM-Token`.
