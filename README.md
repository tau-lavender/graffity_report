# Graffity Report Telegram mini-app
## Короткое описание
Приложение позволяет отправить фотографию и адрес незаконного граффити. После обработки заявки модерацией, в администрацию района будет отправлена заявка на удаление. Статус своей заявки можно отслеживать.

---
# Start
## На сервере
Запуск через railway
## Локально
Поменять ENV в docs/config.js на 'local'
``` bash
docker compose build
docker compose up
```
*Не полностью поддерживается*

---

# Стек
- python (uv)
- flask
- html + css + js
- PostgreSQL + PostGis + DADATA
- docker
