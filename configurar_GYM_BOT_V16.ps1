# Ejecutar desde la carpeta del proyecto.
# Crea .env desde .env.example si aún no existe; no sobrescribe secretos existentes.
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Se creó .env. Ábrelo y completa tus llaves sandbox, precio y URL HTTPS." -ForegroundColor Yellow
} else {
    Write-Host ".env ya existe; no se modificó." -ForegroundColor Green
}
python -c "import secrets; print('Secreto sugerido para GYMBOT_SESSION_SECRET:'); print(secrets.token_urlsafe(48))"
Write-Host "No pegues tus llaves privadas en el chat. Guárdalas solo en .env." -ForegroundColor Cyan
