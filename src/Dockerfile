
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем requirements из папки src, т.к. Railway берет корень репо как build context
COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только исходники backend
COPY src/ ./src

# Указываем порт через переменную $PORT (Railway задаёт его автоматически)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=5000
EXPOSE 5000

# Запуск через gunicorn без смены директории, указываем модуль как src.main:app
# Используем shell-форму CMD для раскрытия переменной $PORT
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level info --access-logfile - --error-logfile - src.main:app
