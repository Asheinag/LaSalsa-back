#!/bin/sh
set -e

# 1. Ждем базу (твой надежный цикл)
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT} ..."
for i in $(seq 1 60); do
  if nc -z "${DB_HOST}" "${DB_PORT}" 2>/dev/null; then
    echo "Postgres is up"
    break
  fi
  sleep 1
done

# 2. Прогоняем миграции ТОЛЬКО если это бэкенд
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running migrations..."
  alembic upgrade head
fi

# 3. Запускаем то, что пришло из docker-compose (uvicorn или celery)
echo "Starting command: $@"
exec "$@"