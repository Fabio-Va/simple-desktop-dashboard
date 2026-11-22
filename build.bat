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
rem librerie: le scarico solo la prima volta o quando requirements.txt cambia
fc /b requirements.txt ".build\requirements.done" >nul 2>nul
if errorlevel 1 (
  echo  [2/3] Scarico le librerie...
  ".build\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q --upgrade pip
  ".build\venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt pyinstaller || goto :errore
  copy /y requirements.txt ".build\requirements.done" >nul
) else (
  echo  [2/3] Librerie gia' aggiornate.
)

echo  [3/3] Compilo...
rem compilo in .build\dist (SiDD resta aperta e usabile), riusando l'analisi del build precedente;
rem la ricetta e' sidd.spec, che lascia fuori le parti di Qt che SiDD non usa
if exist ".build\work\Dashboard" rmdir /s /q ".build\work\Dashboard"
".build\venv\Scripts\pyinstaller.exe" --noconfirm --log-level WARN --workpath ".build\work" --distpath ".build\dist" "%~dp0sidd.spec" || goto :errore

rem solo adesso chiudo SiDD, aspetto che liberi davvero SiDD.exe e lo sostituisco (fino a 15 secondi)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Stop-Process -Name SiDD,Dashboard -Force -ErrorAction SilentlyContinue; for($i=0;$i -lt 30;$i++){ try{ Copy-Item '%~dp0.build\dist\SiDD.exe' '%~dp0SiDD.exe' -Force -ErrorAction Stop; exit 0 } catch { Start-Sleep -Milliseconds 500 } }; exit 1" || goto :errore

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
rem Start-Process e non "start": cosi' SiDD non resta agganciata alla finestra del build
powershell -NoProfile -Command "Start-Process -FilePath '%~dp0SiDD.exe' -WorkingDirectory '%~dp0'"
timeout /t 4 >nul
exit /b 0

:errore
echo.
echo  Qualcosa e' andato storto: leggi il messaggio qui sopra.
pause
exit /b 1
