# GraffitiReport - Переключение между локальной разработкой и production

## Быстрое переключение URL

### Для локальной разработки:
Откройте `docs/config.js` и установите:
```javascript
const ENV = 'local';
```

### Для деплоя (GitHub Pages + Railway):
Откройте `docs/config.js` и установите:
```javascript
const ENV = 'production';
```

И обновите production URL после деплоя на Railway:
```javascript
const API_ENDPOINTS = {
    local: 'http://localhost:5000',
    production: 'https://your-app-name.railway.app' // Замените на ваш URL
};
```

## Проверка работы GitHub Pages

GitHub Pages автоматически публикует содержимое папки `docs/` на:
- `https://tau-lavender.github.io/graffity_report/`
- Админ панель: `https://tau-lavender.github.io/graffity_report/admin.html`

**Важно:** GitHub Pages работает только с фронтендом (HTML/CSS/JS). Для работы приложения нужен backend на Railway.
