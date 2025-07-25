# Используем легковесный образ Python 3.13
FROM python:3.13-slim

# Устанавливаем необходимые зависимости
RUN apt-get update && apt-get install -y \
    build-essential

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем json для firebase
COPY serviceAccountKey.json .

# Копируем код приложения в контейнер
COPY ./app ./app
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]