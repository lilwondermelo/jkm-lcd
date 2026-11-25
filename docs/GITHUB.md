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
git remote add origin https://github.com/<USER>/jkm-lcd.git
git push -u origin HEAD
git tag v3.0.0 && git push --tags
```

Имя `<USER>` возьму из самого токена (`GET /user`), угадывать не буду.

Альтернатива без токена в файле: скачать `gh` в `~/.local/bin`, сделать
`gh auth login` и работать через `gh`.
