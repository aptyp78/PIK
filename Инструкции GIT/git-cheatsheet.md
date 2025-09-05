# Инструкции по работе с Git

## Основной рабочий цикл

```bash
# Подтянуть изменения из GitHub перед началом работы
git pull origin main

# Проверить состояние рабочего каталога
git status

# Добавить измененные или новые файлы в индекс
git add .

# Сделать коммит с комментарием
git commit -m "Краткое описание изменений"

# Отправить изменения в удалённый репозиторий
git push origin main
```

## Развернутый цикл с проверками

```bash
# Проверить текущую ветку
git branch

# Обновить локальную ветку свежими изменениями с GitHub
git pull origin main

# Добавить конкретный файл ( если нужен выборочно)
git add path/to/file

# или добавить все изменения
git add .

# Сделать коммит с лаконичным сообщением
git commit -m "Описание изменений"

# Отправить коммит на сервер
git push origin main
```

## Дополнительные команды

```bash
# Просмотр удалённых репозиториев
git remote -v

# Смена URL для origin
git remote set-url origin git@github.com:ваш_логин/PIK.git

# Создание новой ветки
git checkout -b feature-branch

# Слияние ветки feature-branch с main
git checkout main
git merge feature-branch

# Удаление локальной ветки
git branch -d feature-branch
```
