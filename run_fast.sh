#!/bin/bash

# Script optimizado para ejecutar con cache del modelo
# Evita recargar el modelo en cada ejecución

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
CACHE_DIR="/tmp/whisper_model_cache"
MODEL_NAME="${WHISPER_MODEL:-base}"

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Procesador de Audio a Texto - Modo Rápido${NC}"
    echo ""
    echo "Uso: $0 [fecha_inicio] [fecha_fin] [opciones]"
    echo ""
    echo "Este script optimiza la carga del modelo Whisper usando cache"
    echo ""
    echo "Argumentos:"
    echo "  fecha_inicio    Fecha de inicio en formato YYYY-MM-DD"
    echo "  fecha_fin       Fecha de fin en formato YYYY-MM-DD"
    echo ""
    echo "Opciones:"
    echo "  --dry-run       Solo mostrar qué se procesaría"
    echo "  --json          Generar reporte en formato JSON"
    echo "  --query SQL     Usar consulta SQL personalizada"
    echo "  --build         Reconstruir la imagen Docker"
    echo "  --logs          Mostrar logs en tiempo real"
    echo "  --help          Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 2024-01-01 2024-01-31"
    echo "  $0 2024-01-01 2024-01-31 --dry-run"
    echo "  $0 2024-01-01 2024-01-31 --json"
}

# Función para validar fecha
validate_date() {
    if [[ $1 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        return 0
    else
        echo -e "${RED}Error: Formato de fecha inválido: $1${NC}"
        echo "Use el formato YYYY-MM-DD"
        return 1
    fi
}

# Función para construir comando optimizado
build_optimized_command() {
    local start_date=$1
    local end_date=$2
    shift 2
    
    # Usar docker-compose con cache
    local cmd="docker compose -f docker-compose.cache.yml run --rm audio-to-text python main.py --start-date $start_date --end-date $end_date"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                cmd="$cmd --dry-run"
                shift
                ;;
            --json)
                cmd="$cmd --output-format json"
                shift
                ;;
            --query)
                if [[ -n $2 ]]; then
                    cmd="$cmd --query \"$2\""
                    shift 2
                else
                    echo -e "${RED}Error: --query requiere un valor${NC}"
                    exit 1
                fi
                ;;
            *)
                echo -e "${RED}Error: Opción desconocida: $1${NC}"
                exit 1
                ;;
        esac
    done
    
    echo "$cmd"
}

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker no está instalado${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose no está instalado${NC}"
    exit 1
fi

# Procesar argumentos
if [[ $# -eq 0 ]] || [[ $1 == "--help" ]]; then
    show_help
    exit 0
fi

# Verificar si se debe reconstruir
if [[ $1 == "--build" ]]; then
    echo -e "${YELLOW}Reconstruyendo imagen Docker con cache...${NC}"
    docker compose -f docker-compose.cache.yml build
    shift
fi

# Verificar si se deben mostrar logs
if [[ $1 == "--logs" ]]; then
    echo -e "${YELLOW}Mostrando logs en tiempo real...${NC}"
    docker compose -f docker-compose.cache.yml logs -f
    exit 0
fi

# Verificar argumentos mínimos
if [[ $# -lt 2 ]]; then
    echo -e "${RED}Error: Se requieren fecha de inicio y fecha de fin${NC}"
    echo "Use --help para ver la ayuda"
    exit 1
fi

# Validar fechas
if ! validate_date "$1" || ! validate_date "$2"; then
    exit 1
fi

start_date=$1
end_date=$2
shift 2

# Verificar que existe archivo .env
if [[ ! -f .env ]]; then
    echo -e "${YELLOW}Advertencia: No se encontró archivo .env${NC}"
    echo "Copiando env.example a .env..."
    cp env.example .env
    echo -e "${YELLOW}Por favor, edita .env con tu configuración antes de continuar${NC}"
    exit 1
fi

# Crear directorio de cache si no existe
mkdir -p "$CACHE_DIR"

# Construir comando optimizado
command=$(build_optimized_command "$start_date" "$end_date" "$@")

echo -e "${GREEN}🚀 Ejecutando procesamiento optimizado de audio a texto...${NC}"
echo -e "${BLUE}📅 Período: $start_date a $end_date${NC}"
echo -e "${BLUE}🤖 Modelo: $MODEL_NAME (con cache)${NC}"
echo -e "${BLUE}⚡ Comando: $command${NC}"
echo ""

# Ejecutar comando
eval $command

# Verificar resultado
if [[ $? -eq 0 ]]; then
    echo -e "${GREEN}✅ Procesamiento completado exitosamente${NC}"
elif [[ $? -eq 1 ]]; then
    echo -e "${YELLOW}⚠️  Procesamiento completado con algunos errores${NC}"
else
    echo -e "${RED}❌ Procesamiento falló${NC}"
fi

echo ""
echo -e "${BLUE}📁 Archivos generados:${NC}"
echo "  - Audios: ./audios/"
echo "  - Transcripciones: ./textos/"
echo "  - Logs: ./logs/"
echo ""
echo -e "${GREEN}💡 Tip: El modelo se mantiene en cache para futuras ejecuciones${NC}"
