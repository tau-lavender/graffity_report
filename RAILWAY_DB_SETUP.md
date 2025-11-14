# Подключение PostgreSQL + PostGIS на Railway

## Что уже сделано

✅ Создан отдельный PostGIS сервис на Railway
✅ PostGIS расширение активно (версия 3.7)
✅ Модели SQLAlchemy созданы (`src/models.py`)
✅ Утилиты для работы с БД (`src/util.py`)
✅ Health endpoint для проверки БД (`/api/db/health`)

## Шаг 1: Настройка переменных окружения в Railway

### На PostGIS сервисе уже есть:
```
POSTGRES_DB=railway
POSTGRES_USER=postgres
POSTGRES_PASSWORD=g1g4b13Ed115Ed6D6GEAgBg2adaCDA56
DATABASE_PRIVATE_URL=postgres://postgres:g1g4b13Ed115Ed6D6GEAgBg2adaCDA56@RAILWAY_PRIVATE_DOMAIN:5432/railway
```

### На Backend сервисе добавьте:

1. **Способ 1 (через DATABASE_URL):**
   ```
   DATABASE_URL=${{PostGIS.DATABASE_PRIVATE_URL}}
   ```
   - Где `PostGIS` — имя вашего PostGIS сервиса в Railway
   - Railway автоматически подставит приватный URL

2. **Способ 2 (отдельные переменные):**
   ```
   DB_HOST=${{PostGIS.RAILWAY_PRIVATE_DOMAIN}}
   DB_PORT=5432
   DB_NAME=${{PostGIS.POSTGRES_DB}}
   DB_USER=${{PostGIS.POSTGRES_USER}}
   DB_PASSWORD=${{PostGIS.POSTGRES_PASSWORD}}
   ```

**Рекомендую Способ 1** — проще и надежнее.

## Шаг 2: Выполнить миграцию схемы БД

### Вариант А: Через SQL консоль Railway (быстро)

1. Railway → PostGIS сервис → вкладка "Data" или "Query"
2. Вставьте содержимое `init_db.sql` и выполните
3. Проверьте таблицы:
   ```sql
   \dt
   SELECT * FROM users LIMIT 1;
   ```

### Вариант Б: Через psql локально

```powershell
# Получите DATABASE_URL из PostGIS сервиса в Railway (вкладка Variables)
$env:DATABASE_URL="postgres://postgres:g1g4b13Ed115Ed6D6GEAgBg2adaCDA56@PROXY_DOMAIN:PROXY_PORT/railway"

# Выполните миграцию
psql $env:DATABASE_URL -f init_db.sql
```

### Вариант В: Автоматически из Python (удобно для деплоя)

В `src/main.py` добавьте перед `if __name__`:

```python
from src.util import init_db

# Инициализация БД при старте (создаст таблицы если их нет)
with app.app_context():
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database init warning: {e}")
```

## Шаг 3: Проверка подключения

После деплоя на Railway откройте:

1. **Health check базы:**
   ```
   https://graffityreport-production.up.railway.app/api/db/health
   ```

   Должен вернуть:
   ```json
   {
     "ok": true,
     "postgres": "PostgreSQL 15.x ...",
     "postgis": "3.7 USE_GEOS=1 USE_PROJ=1 USE_STATS=1"
   }
   ```

2. **Общий health:**
   ```
   https://graffityreport-production.up.railway.app/health
   ```

## Шаг 4: Переключение с Singleton на БД

После успешного подключения обновите `src/app/admin/admin_routes.py`:

### Было (Singleton):
```python
from src.singleton import SingletonClass
singleton = SingletonClass()

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    return jsonify(singleton.applications)
```

### Станет (PostgreSQL):
```python
from src.util import get_db_session
from src.models import GraffitiReport, User

@admin_bp.route('/api/applications', methods=['GET'])
def get_applications():
    session = get_db_session()
    user_id = request.args.get('telegram_user_id')

    query = session.query(GraffitiReport)
    if user_id:
        query = query.join(User).filter(User.telegram_user_id == int(user_id))

    reports = query.all()
    return jsonify([{
        'id': r.id,
        'location': r.address,
        'comment': r.comment,
        'status': r.status,
        'telegram_username': r.user.telegram_username if r.user else None,
        'created_at': r.created_at.isoformat()
    } for r in reports])
```

## Шаг 5: Локальное тестирование (опционально)

Если хотите тестировать локально с Railway БД:

```powershell
# Установите переменную DATABASE_URL из Railway (PUBLIC URL для внешнего доступа)
$env:DATABASE_URL="postgres://postgres:PASSWORD@TCP_PROXY_DOMAIN:TCP_PROXY_PORT/railway"

# Запустите бэкенд
cd src
python main.py
```

Откройте: http://localhost:5000/api/db/health

## Шаг 6: Добавление фото (MinIO/S3)

После настройки БД можно подключить хранилище фото:

1. **Cloudflare R2** (рекомендую):
   - Бесплатный egress
   - S3-совместимый API
   - Переменные: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET, S3_ENDPOINT_URL

2. **MinIO на Railway**:
   - Создать отдельный сервис с образом `minio/minio`
   - Добавить Volume для /data
   - Переменные: MINIO_ROOT_USER, MINIO_ROOT_PASSWORD

## Быстрая проверка

После настройки всех переменных и деплоя:

```bash
# 1. Проверка БД
curl https://graffityreport-production.up.railway.app/api/db/health

# 2. Проверка приложений (должен вернуть пустой массив или данные)
curl https://graffityreport-production.up.railway.app/api/applications

# 3. Создание тестовой заявки
curl -X POST https://graffityreport-production.up.railway.app/api/apply \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Test Location",
    "comment": "Test comment",
    "telegram_user_id": 123456,
    "telegram_username": "testuser"
  }'
```

## Troubleshooting

### Ошибка "relation does not exist"
- Таблицы не созданы → выполните `init_db.sql`

### Ошибка "could not connect to server"
- Проверьте DATABASE_URL в переменных бэкенда
- Убедитесь, что используете PRIVATE_URL внутри Railway

### Ошибка "function postgis_version() does not exist"
- PostGIS не установлен → выполните `CREATE EXTENSION IF NOT EXISTS postgis;`

### Health endpoint возвращает "DATABASE_URL is not set"
- Добавьте переменную DATABASE_URL в Railway → Backend → Variables

## Готово! 🎉

Теперь ваше приложение:
- ✅ Использует PostgreSQL с PostGIS
- ✅ Хранит заявки в БД (не теряются при рестарте)
- ✅ Поддерживает геолокацию (POINT geometry)
- ✅ Готово к добавлению фото через S3/MinIO
