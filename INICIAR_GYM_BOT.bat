@echo off
chcp 65001 >nul
title GYM BOT V15 - Premium
cd /d "%~dp0"
echo ==============================================
echo       GYM BOT - Entrenamiento inteligente
echo ==============================================
python --version
if errorlevel 1 (
  echo ERROR: Python no esta instalado o no esta en PATH.
  pause
  exit /b 1
)
echo.
echo Iniciando GYM BOT...
python GYM_BOT_V14_VIDEO_READY.py
pause
