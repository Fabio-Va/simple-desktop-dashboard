@echo off
cd /d "%~dp0"
if not exist ".build\venv\Scripts\pythonw.exe" (
  echo Prima esegui build.bat una volta.
  pause
  exit /b 1
)
start "" ".build\venv\Scripts\pythonw.exe" sidd.py
