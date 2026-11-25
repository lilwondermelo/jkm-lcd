# Безопасность

- Секреты (device-токены, настройки) хранятся только в файлах с правами
  `600`: `~/.config/jkm-lcd/*`, `~/.local/state/jkm-lcd/*`.
- Токен **никогда** не пишется в APK, PWA, документы и репозиторий.
- Сопряжение: 4-значный код живёт 5 минут и одноразовый; телефон получает
  случайный device-token (24 байта hex), который можно отозвать.
- `jkmctl require-token on` включает обязательный заголовок `X-JKM-Token`
  для удалённых запросов. Локальные запросы с 127.0.0.1 остаются без токена —
  CLI работает без секрета.
- Операторские порты (8090, 8180 и т.п.) не публикуются наружу; в nginx
  открываются только сайты, `/repo/`, `/films/`.
- Keystore подписи APK (`~/fdroid/keystore/kuler-release.jks`) не пересоздаётся
  при выпуске: иначе обновление не встанет поверх установленного приложения.
- `versionCode` растёт; подпись — release-ключом, не debug.


> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.
