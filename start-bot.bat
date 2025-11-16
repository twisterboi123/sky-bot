@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PY=%SCRIPT_DIR%.venv\Scripts\python.exe"
set "BOT=%SCRIPT_DIR%bot.py"

if exist "%PY%" (
  "%PY%" "%BOT%"
) else (
  echo Virtual env not found; using system Python
  python "%BOT%"
)
