# PowerShell скрипт для замены старого URL на новый URL Amvera

# ВАЖНО: Замените YOUR_PROJECT_NAME на реальное имя проекта в Amvera
$NEW_URL = "https://YOUR_PROJECT_NAME.amvera.io"
$OLD_URL = "https://thefid.pythonanywhere.com"

Write-Host "🔄 Замена URL с $OLD_URL на $NEW_URL" -ForegroundColor Cyan

# Замена в app.js
$appJsPath = "docs\app.js"
(Get-Content $appJsPath) -replace [regex]::Escape($OLD_URL), $NEW_URL | Set-Content $appJsPath
Write-Host "✅ Обновлен docs\app.js" -ForegroundColor Green

# Замена в admin.html
$adminHtmlPath = "docs\admin.html"
(Get-Content $adminHtmlPath) -replace [regex]::Escape($OLD_URL), $NEW_URL | Set-Content $adminHtmlPath
Write-Host "✅ Обновлен docs\admin.html" -ForegroundColor Green

Write-Host "`n🎉 Готово! Не забудьте закоммитить изменения:" -ForegroundColor Yellow
Write-Host "  git add docs\app.js docs\admin.html"
Write-Host "  git commit -m 'Update API URL to Amvera'"
Write-Host "  git push origin main"
