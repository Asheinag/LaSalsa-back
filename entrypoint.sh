#!/bin/sh

# Если передана команда, выполнить её напрямую
if [ $# -gt 0 ]; then
    echo "Выполняем команду: $@"
    exec "$@"
fi

# Иначе стандартный запуск для FastAPI
echo "Ждём БД..."
sleep 10
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000