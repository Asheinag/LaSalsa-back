#!/bin/sh
echo "Ждём БД..."
sleep 10
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000