FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем requirements из папки src
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники backend
COPY src/ ./src

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Явно укажем порт для платформ, которые определяют порт через EXPOSE
EXPOSE 8080

# Запуск через gunicorn: используем $PORT, если задан, иначе 8080 (для Docker-платформ)
CMD sh -c "BIND_PORT=\${PORT:-8080} && echo Using port \$BIND_PORT && gunicorn --bind 0.0.0.0:\$BIND_PORT --workers 2 --timeout 120 --log-level info --access-logfile - --error-logfile - src.main:app"
