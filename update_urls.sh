#!/bin/bash
# Скрипт для замены старого URL на новый URL Amvera

# ВАЖНО: Замените YOUR_PROJECT_NAME на реальное имя проекта в Amvera
NEW_URL="https://YOUR_PROJECT_NAME.amvera.io"
OLD_URL="https://thefid.pythonanywhere.com"

echo "🔄 Замена URL с $OLD_URL на $NEW_URL"

# Замена в app.js
sed -i "s|$OLD_URL|$NEW_URL|g" docs/app.js
echo "✅ Обновлен docs/app.js"

# Замена в admin.html
sed -i "s|$OLD_URL|$NEW_URL|g" docs/admin.html
echo "✅ Обновлен docs/admin.html"

echo "🎉 Готово! Не забудьте закоммитить изменения:"
echo "  git add docs/app.js docs/admin.html"
echo "  git commit -m 'Update API URL to Amvera'"
echo "  git push origin main"
