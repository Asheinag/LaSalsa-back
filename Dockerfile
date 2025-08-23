# Используем легковесный образ Python 3.13
FROM python:3.13-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*


# Базовые настройки Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения в контейнер
COPY ./app ./app
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

# Non-root пользователь
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# entrypoint
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]