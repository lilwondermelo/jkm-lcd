# Публикация на GitHub от имени владельца

Токен не должен попадать в чат, репозиторий или APK.

1. Открой https://github.com/settings/tokens/new
2. Создай classic token с правами `repo` (и `workflow`, если понадобятся Actions).
3. Положи токен в файл:

```bash
mkdir -p ~/.config/jkm-lcd
printf '%s\n' 'ТОКЕН' > ~/.config/jkm-lcd/github_token
chmod 600 ~/.config/jkm-lcd/github_token
```

4. Скажи только, что файл готов — я возьму токен из файла и сделаю:

```bash
git remote add origin https://github.com/lilwondermelo/jkm-lcd.git
git push -u origin HEAD
git tag v3.0.0 && git push --tags
```

Имя `lilwondermelo` возьму из самого токена (`GET /user`), угадывать не буду.

Альтернатива без токена в файле: скачать `gh` в `~/.local/bin`, сделать
`gh auth login` и работать через `gh`.

## Репозиторий

Публичный: https://github.com/lilwondermelo/jkm-lcd
APK в репозитории: `apk/com.arch.kuler_18.apk`, также как asset в релизе v3.0.1.

## Что нужно от владельца для AUR и npm

**AUR** (токен не нужен, нужен SSH-ключ):
1. Создай аккаунт https://aur.archlinux.org/register (логин `lilwondermelo` или любой).
2. Добавь публичный ключ сервера в https://aur.archlinux.org/account/:
   `cat ~/.ssh/id_ed25519.pub` — скопируй **только публичный** ключ.
   Если ключа нет: `ssh-keygen -t ed25519` (без passphrase для автоматической загрузки).
3. Скажи логин — я добавлю PKGBUILD в isolated AUR repo и запушу через SSH.

**npm** (нужен токен):
1. Создай аккаунт https://www.npmjs.com/signup.
2. Создай granular token с правом **publish** на пакет `@arch-home/jkm-lcd`:
   https://www.npmjs.com/settings/<твой-логин>/tokens/new
3. Положи токен в `~/.config/jkm-lcd/npm_token` (600) и скажи только путь.
   Я переменную `GITHUB_USER`/scope в `package.json` заменю на твой npm-логин
   и сделаю `npm publish` через `NPM_CONFIG_//registry.npmjs.org/:_authToken`.


> Note: VID/PID `1a86:5722` and `9600 8N1` are for one particular display model, not universal. Check `lsusb` and your device docs. CDC-ACM just means the USB port appears as a serial (COM) port. Replace `<HOST>` and `<PORT>` with your own values.

Опубликовано: https://www.npmjs.com/package/@lilwondermelo/jkm-lcd

```bash
npm i -g @lilwondermelo/jkm-lcd
jkmctl doctor
```
