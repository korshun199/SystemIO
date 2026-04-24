#!/bin/bash

# --- НАСТРОЙКИ ---
REMOTE_USER="oleg"
REMOTE_HOST="46.8.221.179"
REMOTE_PATH="/home/work/SystemIO/base.db"
COMMIT_MSG=$1

if [ -z "$COMMIT_MSG" ]
then
      COMMIT_MSG="Sync: full structure update $(date +'%Y-%m-%d %H:%M')"
fi

echo "🚀 Начинаем зеркальную синхронизацию в ветку admin-dev..."

# 1. Работа с ГИТОМ (Зеркальный режим)
# Флаг -A (или --all) принудительно обновляет индекс: 
# добавляет новые, фиксирует изменения и УДАЛЯЕТ то, что ты удалил локально.
git add -A 

git commit -m "$COMMIT_MSG"
git push origin admin-dev

echo "✅ Гит полностью синхронизирован (удаленные файлы стерты и в облаке)"

# 2. Передача базы по SSH
echo "📦 Отправляем базу на VPS..."
scp -P 4101 ./base.db $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH

if [ $? -eq 0 ]; then
    echo "✅ База доставлена в $REMOTE_PATH"
else
    echo "❌ Ошибка при передаче базы!"
fi

echo "🎉 Синхронизация завершена успешно!"