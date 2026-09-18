@echo off
chcp 65001 >nul
cd /d "%~dp0"
py -3 -m aurora 2>nul
if errorlevel 1 python -m aurora
if errorlevel 1 (
  echo.
  echo Нужен Python 3.10+  https://www.python.org/downloads/
  pause
)
