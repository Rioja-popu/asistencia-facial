@echo off
rem Crea en el escritorio el acceso directo "Asistencia Docente IES 7".
rem Ejecutar una sola vez, con doble clic, despues de instalar (ver README).
setlocal
set "RAIZ=%~dp0"
if not exist "%RAIZ%.venv\Scripts\pythonw.exe" (
    echo No se encontro el entorno virtual .venv. Segui primero los pasos de instalacion del README.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$raiz = $env:RAIZ.TrimEnd('\');" ^
  "$destino = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Asistencia Docente IES 7.lnk';" ^
  "$acceso = (New-Object -ComObject WScript.Shell).CreateShortcut($destino);" ^
  "$acceso.TargetPath = Join-Path $raiz '.venv\Scripts\pythonw.exe';" ^
  "$acceso.Arguments = '\"' + (Join-Path $raiz 'src\iniciar.py') + '\"';" ^
  "$acceso.WorkingDirectory = $raiz;" ^
  "$acceso.IconLocation = Join-Path $raiz 'assets\escudo.ico';" ^
  "$acceso.Description = 'Asistencia Docente - IES N. 7 Populorum Progressio';" ^
  "$acceso.Save(); Write-Host ('Acceso directo creado: ' + $destino)"
if errorlevel 1 (
    echo No se pudo crear el acceso directo.
    pause
    exit /b 1
)
pause
