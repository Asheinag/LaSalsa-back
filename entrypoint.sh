#!/bin/sh
set -e

# Если передали явную команду — выполняем её (для миграций/отладки)
if [ "$#" -gt 0 ]; then
  echo "Run custom command: $*"
  exec "$@"
fi

# Проверим, что задано имя/порт БД (или подставь свои env)
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."
# ждём БД (до 60 сек)
for i in $(seq 1 60); do
  if nc -z "${DB_HOST}" "${DB_PORT}" 2>/dev/null; then
    echo "Postgres is up"
    break
  fi
  sleep 1
done

# Прогоним миграции Alembic
# Если alembic.ini лежит в /app — просто:
alembic upgrade head

# Запускаем API
exec uvicorn app.main:app --host 0.0.0.0 --port 8000