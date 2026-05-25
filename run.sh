#!/usr/bin/env bash
# ============================================================
#  Setup GPU (cuML / RAPIDS) dentro de WSL2 - Palmer Penguins
#  Invocado por run.bat cuando se detecta GPU NVIDIA + WSL2.
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/.venvs/mineria"

cd "$PROJECT_DIR"

echo "============================================"
echo "  WSL2 GPU setup - cuML / RAPIDS"
echo "============================================"
echo "Proyecto: $PROJECT_DIR"
echo "Venv WSL: $VENV_DIR"
echo

# ------------------------------------------------------------
# [1/5] Verificar / instalar Python3 + venv + pip
# ------------------------------------------------------------
echo "[1/5] Verificando Python3..."
if ! command -v python3 >/dev/null 2>&1 || ! python3 -m venv --help >/dev/null 2>&1; then
    echo "     Instalando python3, venv y pip (sudo apt)..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv
fi
PYVER=$(python3 --version | awk '{print $2}')
echo "     Python $PYVER OK."
echo

# ------------------------------------------------------------
# [2/5] Verificar acceso a la GPU desde WSL2
# ------------------------------------------------------------
echo "[2/5] Verificando GPU dentro de WSL2..."
if ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "     ERROR: nvidia-smi no esta disponible en WSL2."
    echo "     Necesitas el driver NVIDIA para Windows (>=470) con soporte WSL."
    echo "     Descarga: https://www.nvidia.com/Download/index.aspx"
    exit 1
fi
nvidia-smi -L
CUDA_VER=$(nvidia-smi 2>/dev/null | grep -oP 'CUDA Version: \K[0-9]+' | head -n1)
CUDA_VER=${CUDA_VER:-12}
echo "     CUDA runtime soportado: ${CUDA_VER}.x"
echo

# ------------------------------------------------------------
# [3/5] Crear / reutilizar entorno virtual en filesystem WSL
# ------------------------------------------------------------
echo "[3/5] Preparando entorno virtual..."
FRESH_VENV=0
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    mkdir -p "$(dirname "$VENV_DIR")"
    python3 -m venv "$VENV_DIR"
    FRESH_VENV=1
    echo "     venv creado en $VENV_DIR"
else
    echo "     venv existente reutilizado."
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo

# ------------------------------------------------------------
# [4/5] Instalar dependencias base + cuML del indice NVIDIA
# ------------------------------------------------------------
echo "[4/5] Instalando dependencias..."
if [ "$FRESH_VENV" -eq 1 ]; then
    pip install --upgrade pip --quiet
    pip install -r requirements.txt
    echo "     Instalando cuML (RAPIDS) para CUDA ${CUDA_VER}.x..."
    if [ "$CUDA_VER" -ge 12 ]; then
        pip install --extra-index-url=https://pypi.nvidia.com "cuml-cu12"
    else
        pip install --extra-index-url=https://pypi.nvidia.com "cuml-cu11"
    fi
else
    pip install -r requirements.txt --quiet
    if ! pip show cuml >/dev/null 2>&1; then
        echo "     cuML no instalado en venv existente. Instalando..."
        if [ "$CUDA_VER" -ge 12 ]; then
            pip install --extra-index-url=https://pypi.nvidia.com "cuml-cu12"
        else
            pip install --extra-index-url=https://pypi.nvidia.com "cuml-cu11"
        fi
    fi
fi
echo "     Dependencias listas."
echo

# ------------------------------------------------------------
# [5/5] Lanzar Jupyter con cuml.accel activo (parchea sklearn)
# ------------------------------------------------------------
echo "[5/5] Iniciando Jupyter con aceleracion GPU (cuml.accel)..."
echo "     Abre en el navegador: http://localhost:8888/lab"
echo "     (Ctrl+C aqui para detener Jupyter.)"
echo

# `python -m cuml.accel` parchea sklearn automaticamente: KMeans,
# DBSCAN y AgglomerativeClustering corren en GPU sin tocar el notebook.
exec python -m cuml.accel -m jupyter notebook notebook.ipynb \
    --ip=0.0.0.0 --port=8888 --no-browser \
    --ServerApp.token='' --ServerApp.password=''
