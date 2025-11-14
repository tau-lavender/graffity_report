# Установка PostGIS на Railway Managed PostgreSQL

## Текущая ситуация
✅ PostgreSQL 17.6 работает
❌ PostGIS не установлен

## Шаг 1: Подключитесь к БД

### Через Railway SQL Console:
1. Railway → PostgreSQL сервис → вкладка "Data" или "Query"
2. Откроется встроенный SQL редактор

### Или через psql локально:
```powershell
# Найдите DATABASE_PUBLIC_URL в Variables вашего PostgreSQL сервиса
# Формат: postgresql://postgres:PASSWORD@DOMAIN:PORT/railway

psql "postgresql://postgres:YOUR_PASSWORD@proxy.railway.app:12345/railway"
```

## Шаг 2: Установите PostGIS

Выполните в SQL консоли:

```sql
-- Установка расширения
CREATE EXTENSION IF NOT EXISTS postgis;

-- Проверка версии
SELECT PostGIS_Version();

-- Дополнительные расширения (опционально, но полезно)
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;
```

## Шаг 3: Проверка

После выполнения команд проверьте endpoint:
```
https://graffityreport-production.up.railway.app/api/db/health
```

Должен вернуть:
```json
{
  "ok": true,
  "postgres": "PostgreSQL 17.6...",
  "postgis": "3.x USE_GEOS=1 USE_PROJ=1 USE_STATS=1"
}
```

## Возможные проблемы

### Ошибка: "extension postgis is not available"

Managed PostgreSQL на Railway может не поддерживать PostGIS расширение.

**Решение: использовать PostGIS контейнер**

1. **Создайте новый сервис в Railway:**
   - "New" → "Docker Image"
   - Image: `postgis/postgis:15-3.3`

2. **Environment Variables:**
   ```
   POSTGRES_DB=railway
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=создайте_надежный_пароль
   ```

3. **Add Volume:**
   - Settings → Volumes → Add Volume
   - Mount Path: `/var/lib/postgresql/data`
   - Size: 5GB (или больше)

4. **Networking:**
   - Settings → Networking
   - Expose Port: 5432 (Private)
   - Service Name: `postgis` (запомните)

5. **В Backend Variables добавьте:**
   ```
   DATABASE_URL=postgresql://${{postgis.POSTGRES_USER}}:${{postgis.POSTGRES_PASSWORD}}@${{postgis.RAILWAY_PRIVATE_DOMAIN}}:5432/${{postgis.POSTGRES_DB}}
   ```

6. **После деплоя PostGIS сервиса:**
   - Откройте SQL консоль (через Railway Data или psql)
   - Выполните содержимое `init_db.sql`
   - PostGIS уже предустановлен, расширение создастся автоматически при первом `CREATE EXTENSION`

## Итого

- **Попробуйте сначала:** `CREATE EXTENSION postgis;` на managed PostgreSQL
- **Если не работает:** создайте PostGIS контейнер (см. выше)
- **После установки:** перезапустите backend и проверьте `/api/db/health`

Managed база удобнее (автобэкапы, volume автоматически), но если PostGIS недоступен — контейнер будет единственным вариантом.
