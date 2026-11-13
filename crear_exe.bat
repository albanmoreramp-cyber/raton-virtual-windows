@echo off
setlocal
cd /d "%~dp0"
title Crear AI Virtual Mouse.exe
echo ==========================================================
echo    Creando "AI Virtual Mouse.exe"
echo    La primera vez tarda unos minutos. No cierres esta ventana.
echo ==========================================================
echo.

rem --- Buscar Python ---------------------------------------------------------
set "PY=python"
%PY% --version >nul 2>&1
if errorlevel 1 set "PY=py"
%PY% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encuentra Python. Instalalo desde python.org y vuelve a probar.
    goto fin_error
)

rem --- 1. Dependencias -------------------------------------------------------
echo [1/4] Instalando las librerias y PyInstaller...
%PY% -m pip install opencv-python mediapipe pyautogui numpy pystray pillow comtypes pygrabber pyinstaller
if errorlevel 1 goto error_pip

rem --- 2. Modelo de la mano (va DENTRO del .exe) ----------------------------
echo.
echo [2/4] Comprobando el modelo de la mano...
if exist "hand_landmarker.task" goto modelo_ok
echo       Descargando hand_landmarker.task...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task' -OutFile 'hand_landmarker.task'"
if not exist "hand_landmarker.task" goto error_modelo
:modelo_ok
echo       Modelo listo.

rem --- 3. Empaquetar ---------------------------------------------------------
echo.
echo [3/4] Creando el .exe (puede tardar 2-5 minutos)...
set "ICONO="
if exist "icono.ico" set "ICONO=--icon=icono.ico"
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "AI Virtual Mouse" %ICONO% ^
    --collect-all mediapipe ^
    --exclude-module pkg_resources --exclude-module setuptools ^
    --add-data "hand_landmarker.task;." ^
    --add-data "icono.ico;." ^
    --hidden-import pystray._win32 ^
    --collect-submodules comtypes ^
    --hidden-import pygrabber.dshow_graph ^
    raton_virtual.py
if errorlevel 1 goto error_pyinstaller

rem --- 4. Dejar el .exe aqui y limpiar ---------------------------------------
echo.
echo [4/4] Terminando...
copy /y "dist\AI Virtual Mouse.exe" "AI Virtual Mouse.exe" >nul
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "AI Virtual Mouse.spec" 2>nul

echo.
echo ==========================================================
echo    LISTO: "AI Virtual Mouse.exe" esta en esta carpeta.
echo    Haz doble clic en el para usarlo.
echo ==========================================================
pause
exit /b 0

:error_pip
echo.
echo [ERROR] No se pudieron instalar las librerias. Revisa tu conexion a Internet.
goto fin_error
:error_modelo
echo.
echo [ERROR] No se pudo descargar el modelo. Descargalo a mano desde:
echo https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
echo y guardalo en esta carpeta con el nombre hand_landmarker.task
goto fin_error
:error_pyinstaller
echo.
echo [ERROR] PyInstaller ha fallado. Copia el texto de arriba y pasaselo a Claude.
goto fin_error

:fin_error
echo.
pause
exit /b 1
