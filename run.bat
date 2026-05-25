@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

REM =============================================
REM Parseo de argumento: auto (default) | cpu | gpu | help
REM =============================================
set "MODE=%~1"
if "!MODE!"=="" set "MODE=auto"
set "MODE=!MODE:~0,4!"
if /i "!MODE!"=="help" goto :show_help
if /i "!MODE!"=="-h" goto :show_help
if /i "!MODE!"=="/?" goto :show_help

if /i not "!MODE!"=="auto" if /i not "!MODE!"=="cpu" if /i not "!MODE!"=="gpu" (
    echo ERROR: modo desconocido "%~1".
    goto :show_help
)

echo ============================================
echo   Proyecto Mineria - Palmer Penguins
echo   Modo solicitado: !MODE!
echo ============================================
echo.

REM =============================================
REM [1/6] Detectar GPU NVIDIA (siempre, para info)
REM =============================================
echo [1/6] Detectando hardware...
set "HAS_GPU=0"
set "GPU_NAME="

where nvidia-smi >nul 2>&1
if %errorlevel%==0 (
    for /f "delims=" %%i in ('nvidia-smi --query-gpu=name --format=csv,noheader 2^>nul') do (
        if not defined GPU_NAME set "GPU_NAME=%%i"
    )
    if defined GPU_NAME (
        echo      GPU NVIDIA detectada: !GPU_NAME!
        set "HAS_GPU=1"
    )
)
if "!HAS_GPU!"=="0" echo      Sin GPU NVIDIA.
echo.

REM =============================================
REM [2/6] Decidir backend segun MODE
REM =============================================
echo [2/6] Eligiendo backend ^(modo: !MODE!^)...
set "BACKEND=cpu-windows"
set "WSL_READY=0"

REM Probar WSL si el modo lo necesita (gpu o auto con GPU)
if /i "!MODE!"=="gpu" set "PROBE_WSL=1"
if /i "!MODE!"=="auto" if "!HAS_GPU!"=="1" set "PROBE_WSL=1"

if defined PROBE_WSL (
    wsl --status >nul 2>&1
    if !errorlevel!==0 (
        wsl -e echo ok >nul 2>&1
        if !errorlevel!==0 set "WSL_READY=1"
    )
)

if /i "!MODE!"=="cpu" (
    set "BACKEND=cpu-windows"
    echo      Forzado CPU. Backend: scikit-learn-intelex en Windows.
) else if /i "!MODE!"=="gpu" (
    if "!HAS_GPU!"=="0" (
        echo ERROR: Se forzo GPU pero no hay GPU NVIDIA detectada ^(nvidia-smi^).
        exit /b 1
    )
    if "!WSL_READY!"=="0" (
        echo ERROR: Se forzo GPU pero WSL2 no esta listo.
        echo        Instalalo con:  wsl --install ^(PowerShell como admin^), reinicia, reintenta.
        exit /b 1
    )
    set "BACKEND=gpu-wsl"
    echo      Forzado GPU. Backend: cuML/RAPIDS en WSL2.
) else (
    REM auto
    if "!HAS_GPU!"=="1" if "!WSL_READY!"=="1" (
        set "BACKEND=gpu-wsl"
        echo      Auto: GPU disponible. Backend: cuML/RAPIDS en WSL2.
    ) else (
        if "!HAS_GPU!"=="1" (
            echo      Auto: GPU detectada pero WSL2 no esta listo.
            echo        Para usar tu GPU: ejecuta  wsl --install  ^(PowerShell admin^), reinicia.
            echo        O fuerza con:  run.bat gpu
        )
        echo      Auto: Backend: CPU optimizado ^(scikit-learn-intelex^).
    )
)
echo.

REM =============================================
REM [3/6] Ruta GPU/WSL: delegar a run.sh dentro de WSL2
REM =============================================
if "!BACKEND!"=="gpu-wsl" (
    echo [3/6] Convirtiendo ruta a formato WSL...
    for /f "delims=" %%p in ('wsl wslpath -a "%CD%" 2^>nul') do set "WSL_CWD=%%p"
    if not defined WSL_CWD (
        echo ERROR: No se pudo traducir la ruta a WSL. Cayendo a CPU.
        set "BACKEND=cpu-windows"
        goto :cpu_path
    )
    echo      Ruta WSL: !WSL_CWD!
    echo.

    echo [4/6] Lanzando setup en WSL2 ^(esto puede tardar la primera vez^)...
    echo      Se abrira el navegador en http://localhost:8888/lab cuando este listo.
    echo.
    start "" "http://localhost:8888/lab"
    wsl -- bash "!WSL_CWD!/run.sh"
    goto :end
)

:cpu_path
REM =============================================
REM [3/6] Ruta CPU Windows: verificar/instalar Python
REM =============================================
echo [3/6] Verificando Python en Windows...
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo      Python !PYVER! detectado.
    goto :python_ok
)

echo      Python no encontrado. Instalando...
where winget >nul 2>&1
if %errorlevel%==0 (
    echo      Usando winget...
    winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
    if !errorlevel!==0 goto :refresh_path
)

set "PYINSTALLER=%TEMP%\python-installer.exe"
echo      Descargando instalador oficial de Python 3.12.7...
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile '%PYINSTALLER%' -UseBasicParsing; exit 0 } catch { exit 1 }"
if not exist "%PYINSTALLER%" (
    echo ERROR: No se pudo descargar Python.
    pause
    exit /b 1
)
"%PYINSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1
del /q "%PYINSTALLER%" 2>nul

:refresh_path
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python instalado pero no esta en PATH. Cierra y reabre la consola.
    pause
    exit /b 1
)
echo      Python instalado correctamente.

:python_ok
echo.

REM =============================================
REM [4/6] Crear / reutilizar entorno virtual Windows
REM =============================================
echo [4/6] Preparando entorno virtual ^(venv^)...
if not exist "venv\Scripts\activate.bat" (
    python -m venv venv
    if !errorlevel! neq 0 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    set "FRESH_VENV=1"
    echo      venv creado.
) else (
    set "FRESH_VENV=0"
    echo      venv existente reutilizado.
)
call "venv\Scripts\activate.bat"
echo.

REM =============================================
REM [5/6] Instalar dependencias + sklearn-intelex
REM =============================================
echo [5/6] Instalando dependencias...
if "!FRESH_VENV!"=="1" (
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo ERROR: Fallo la instalacion de dependencias base.
        pause
        exit /b 1
    )
    echo      Instalando aceleracion CPU ^(scikit-learn-intelex^)...
    pip install scikit-learn-intelex --quiet
) else (
    pip install -r requirements.txt --quiet
    pip show scikit-learn-intelex >nul 2>&1
    if !errorlevel! neq 0 pip install scikit-learn-intelex --quiet
)
echo      Dependencias listas.
echo.

REM =============================================
REM [6/6] Lanzar Jupyter con sklearn-intelex activo
REM =============================================
echo [6/6] Iniciando Jupyter ^(CPU acelerado con sklearnex^)...
echo.
python -m sklearnex -m jupyter notebook notebook.ipynb

:end
endlocal
exit /b 0

:show_help
echo.
echo Uso: run.bat [modo]
echo.
echo Modos disponibles:
echo   auto   ^(por defecto^)  Detecta GPU+WSL2; si existen usa GPU, si no CPU.
echo   cpu                   Fuerza CPU en Windows ^(scikit-learn-intelex^).
echo   gpu                   Fuerza GPU en WSL2 ^(cuML/RAPIDS^). Falla si no esta listo.
echo   help                  Muestra esta ayuda.
echo.
echo Ejemplos:
echo   run.bat              ^(modo auto^)
echo   run.bat cpu
echo   run.bat gpu
echo.
exit /b 0
