#!/bin/bash

echo "Starting deployment..."

# Создание директории для деплоя
DEPLOY_DIR="/opt/la-salsa"
mkdir -p $DEPLOY_DIR

# Копирование файлов
cp -r . $DEPLOY_DIR/

# Переход в директорию
cd $DEPLOY_DIR

# Установка зависимостей
pip install -r requirements.txt

# Запуск миграций
alembic upgrade head

# Перезапуск сервиса (пример с systemd)
# systemctl restart la-salsa

echo "Deployment completed!"