#!/bin/bash

# --- НАСТРОЙКИ ---
REMOTE_USER="oleg" # Твой пользователь на VPS
REMOTE_HOST="46.8.221.179" # IP твоего сервера
REMOTE_PATH="/home/work/SystemIO/base.db"
COMMIT_MSG=$1

# Проверка, ввел ли ты сообщение для коммита
if [ -z "$COMMIT_MSG" ]
then
      COMMIT_MSG="Admin-dev: sync work $(date +'%Y-%m-%d %H:%M')"
fi

echo "🚀 Начинаем деплой в ветку admin-dev..."

# 1. Работа с ГИТОМ
git add .
git commit -m "$COMMIT_MSG"
git push origin admin-dev

echo "✅ Код отправлен в GitHub/GitLab (ветка admin-dev)"

# 2. Передача базы по SSH (SCP)
echo "📦 Отправляем базу на VPS..."
scp  -P 4101 ./base.db $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH

if [ $? -eq 0 ]; then
    echo "✅ База успешно доставлена в $REMOTE_PATH"
else
    echo "❌ Ошибка при передаче базы!"
fi

echo "🎉 Все операции завершены успешно!"