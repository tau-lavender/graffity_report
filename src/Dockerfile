
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем requirements из папки src, т.к. Railway берет корень репо как build context
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только исходники backend
COPY src/ ./src

# Указываем порт 8080 (Railway использует динамический $PORT, но дефолт 8080)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8080
EXPOSE 8080

# Запуск через gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info --access-logfile - --error-logfile - src.main:app
