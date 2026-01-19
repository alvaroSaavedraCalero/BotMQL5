#!/bin/bash
# Script de inicio para el Bot de Trading Multi-TF
# Multi-TF Scalping Bot for MetaTrader 5

echo "======================================"
echo "  Multi-TF Scalping Bot - Iniciando"
echo "======================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: No se encontró el entorno virtual.${NC}"
    echo "Por favor, ejecuta primero: python3 -m venv venv"
    exit 1
fi

# Activar entorno virtual
echo -e "${YELLOW}[1/3]${NC} Activando entorno virtual..."
source venv/bin/activate

# Verificar dependencias
echo -e "${YELLOW}[2/3]${NC} Verificando dependencias..."
if ! pip show dash > /dev/null 2>&1; then
    echo -e "${RED}Error: Dependencias no instaladas.${NC}"
    echo "Instalando dependencias..."
    cd Python
    pip install -r requirements.txt
    cd ..
fi

# Crear directorios necesarios
echo -e "${YELLOW}[3/3]${NC} Preparando directorios..."
mkdir -p Python/data Python/logs Python/data/mt5_files

# Iniciar aplicación
echo ""
echo -e "${GREEN}Iniciando dashboard y servidor...${NC}"
echo ""
echo "Dashboard disponible en: http://localhost:8050"
echo ""
echo -e "${YELLOW}Nota:${NC} Asegúrate de que MetaTrader 5 esté ejecutándose con el EA activo."
echo ""

cd Python
python main.py
