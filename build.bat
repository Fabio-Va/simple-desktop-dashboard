@echo off
setlocal
cd /d "%~dp0"
title SiDD - build
echo.
echo  Creo SiDD.exe. Ci vogliono qualche minuto la prima volta.
echo.

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (where python >nul 2>nul && set "PY=python")
if not defined PY (
  echo  Python non e' installato. Provo a installarlo con winget...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo  Fatto. Chiudi questa finestra e fai di nuovo doppio click su build.bat.
  pause
  exit /b 1
)

if not exist ".build\venv\Scripts\python.exe" (
  echo  [1/3] Preparo l'ambiente...
  %PY% -m venv ".build\venv" || goto :errore
)
echo  [2/3] Scarico le librerie...
".build\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip
".build\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt pyinstaller || goto :errore

echo  [3/3] Compilo...
rem chiudo SiDD e aspetto che liberi davvero SiDD.exe (fino a 15 secondi), se no PyInstaller non riesce a sostituirlo
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Stop-Process -Name SiDD,Dashboard -Force -ErrorAction SilentlyContinue; $f='%~dp0SiDD.exe'; for($i=0;$i -lt 30;$i++){ if(-not (Test-Path $f)){break}; try{ [IO.File]::Open($f,'Open','ReadWrite','None').Close(); break } catch { Start-Sleep -Milliseconds 500 } }"
".build\venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed --onefile --name SiDD --icon "%~dp0icon.ico" ^
  --collect-submodules recurring_ical_events --collect-data icalendar ^
  --workpath ".build\work" --specpath ".build" --distpath "%~dp0." "%~dp0sidd.py" || goto :errore

rem vecchio nome del progetto: tolgo exe e collegamenti "Dashboard"
if exist "%~dp0Dashboard.exe" del "%~dp0Dashboard.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "foreach($f in 'Desktop','Startup'){ $p=Join-Path ([Environment]::GetFolderPath($f)) 'Dashboard.lnk'; if(Test-Path $p){ Remove-Item $p } }"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dashboard.cmd" del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dashboard.cmd"

echo  Creo il collegamento sul desktop...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'SiDD.lnk')); $s.TargetPath='%~dp0SiDD.exe'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0SiDD.exe,0'; $s.Save()"

echo  La metto in avvio automatico con Windows...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Startup'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'SiDD.lnk')); $s.TargetPath='%~dp0SiDD.exe'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0SiDD.exe,0'; $s.Save()"
echo.
echo  Pronto: trovi "SiDD" sul desktop e si aprira' da sola a ogni avvio di Windows.
echo  La apro adesso.
start "" "%~dp0SiDD.exe"
timeout /t 4 >nul
exit /b 0

:errore
echo.
echo  Qualcosa e' andato storto: leggi il messaggio qui sopra.
pause
exit /b 1
