@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "BACKUPS" mkdir "BACKUPS"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set STAMP=%%i
if not exist "gymbot_v5.db" (
  echo No se encuentra gymbot_v5.db
  pause
  exit /b 1
)
copy /y "gymbot_v5.db" "BACKUPS\gymbot_v5_%STAMP%.db"
if errorlevel 1 (
  echo Error al crear la copia.
) else (
  echo Copia creada en BACKUPS.
)
pause
