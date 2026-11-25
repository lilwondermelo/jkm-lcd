# Выпуск версии

## Сервер / PWA

1.Поднять `VERSION` в `server/main.py`.
2.Проверить: `python3 -m py_compile server/*.py`, `node --check web/app.js`.
3.Перезапустить: `sudo systemctl restart jkm-lcd`, `jkmctl doctor`.
4.Обновить README/CHANGELOG и сделать коммит.

## Android APK

```bash
cd ~/Projects/kuler_lcd/android
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export ANDROID_HOME=/home/Arch/Android/Sdk
./gradlew assembleRelease
~/fdroid/publish.sh kuler
~/fdroid/whatsnew.py set --name kuler --code <versionCode> - <<'TXT'
что увидит пользователь
TXT
```

`versionCode` только растёт; ключ `~/fdroid/keystore/kuler-release.jks`
постоянный. Старая версия на телефоне удаляется один раз (подпись была
потеряна при переезде на новый SSD, #853).

## GitHub / пакеты

- Репозиторий: `https://github.com/<USER>/jkm-lcd`.
- Токен для публикации — в `~/.config/jkm-lcd/github_token` (600); в чат и
  в репозиторий не вставлять.
- AUR: `packaging/arch/PKGBUILD`, npm: `packaging/npm`.

## Чек-лист продакшена

- [ ] `jkmctl doctor` — зелёный, связь с кулером есть.
- [ ] `require-token` включён, телефон привязан по коду.
- [ ] Юнит systemd поправлен под машину, порт не открыт наружу.
- [ ] APK подписан постоянным ключом, `versionCode` больше предыдущего.
- [ ] Документация обновлена (RU + 9 языков).
