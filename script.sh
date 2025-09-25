#!/bin/bash

# Script unificado para procesamiento de audio a texto
# Soporta todas las opciones: CPU, GPU, limpieza automática, cache, etc.

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración por defecto
DEFAULT_COMPOSE_FILE="docker-compose.yml"
DEFAULT_MODE="cpu"
DEFAULT_WORKERS=4
DEFAULT_CHUNK_SIZE=5
DEFAULT_MODEL="tiny"
DEFAULT_CLEANUP="true"

# Función para mostrar ayuda completa
show_help() {
    echo -e "${BLUE}🎵 Procesador de Audio a Texto - Script Unificado${NC}"
    echo ""
    echo "Uso: $0 [comando] [argumentos...]"
    echo ""
    echo "Comandos principales:"
    echo "  process [fecha_inicio] [fecha_fin] [opciones]  Procesar audios"
    echo "  start [fecha_inicio] [fecha_fin] [opciones]    Iniciar servicio y procesar"
    echo "  stop                                          Detener servicios"
    echo "  status                                        Mostrar estado de servicios"
    echo "  logs                                          Mostrar logs en tiempo real"
    echo "  disk-usage                                    Verificar uso de disco"
    echo "  help                                          Mostrar esta ayuda"
    echo ""
    echo "Argumentos para 'process' y 'start':"
    echo "  fecha_inicio    Fecha de inicio en formato YYYY-MM-DD"
    echo "  fecha_fin       Fecha de fin en formato YYYY-MM-DD"
    echo ""
    echo "Opciones de procesamiento:"
    echo "  --mode MODE     Modo de procesamiento (cpu|gpu|cache)"
    echo "  --workers N     Número de workers paralelos (default: 4)"
    echo "  --chunk-size N  Tamaño de chunk para procesamiento (default: 5)"
    echo "  --model MODEL   Modelo Whisper (tiny|base|small|medium|large)"
    echo ""
    echo "Opciones de limpieza:"
    echo "  --cleanup       Habilitar limpieza automática (default)"
    echo "  --no-cleanup    Deshabilitar limpieza automática"
    echo "  --keep-audio    Mantener archivos de audio (no limpiar)"
    echo "  --clean-transcripts Limpiar también transcripciones"
    echo "  --cleanup-delay N Delay en segundos antes de limpiar"
    echo ""
    echo "Opciones de cache:"
    echo "  --cache         Usar cache persistente del modelo"
    echo "  --no-cache      No usar cache (recargar modelo cada vez)"
    echo ""
    echo "Opciones de salida:"
    echo "  --dry-run       Solo mostrar qué se procesaría"
    echo "  --json          Generar reporte en formato JSON"
    echo "  --query SQL     Usar consulta SQL personalizada"
    echo "  --build         Reconstruir la imagen Docker"
    echo "  --logs          Mostrar logs en tiempo real"
    echo ""
    echo "Ejemplos:"
    echo "  $0 process 2024-01-01 2024-01-31"
    echo "  $0 process 2024-01-01 2024-01-31 --mode gpu --model base"
    echo "  $0 process 2024-01-01 2024-01-31 --mode cpu --workers 6 --cleanup"
    echo "  $0 start 2024-01-01 2024-01-31 --mode cache --model small"
    echo "  $0 stop"
    echo "  $0 status"
    echo "  $0 disk-usage"
    echo "  $0 logs"
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

# Función para construir comando con todas las opciones
build_command() {
    local start_date=$1
    local end_date=$2
    shift 2
    
    # Variables por defecto
    local mode="cpu"
    local workers=4
    local chunk_size=5
    local model="tiny"
    local auto_cleanup="true"
    local cleanup_audio="true"
    local cleanup_temp="true"
    local keep_transcripts="true"
    local cleanup_delay=0
    local use_cache="false"
    local compose_file="docker-compose.yml"
    
    # Procesar opciones
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                mode=$2
                shift 2
                ;;
            --workers)
                workers=$2
                shift 2
                ;;
            --chunk-size)
                chunk_size=$2
                shift 2
                ;;
            --model)
                model=$2
                shift 2
                ;;
            --cleanup)
                auto_cleanup="true"
                shift
                ;;
            --no-cleanup)
                auto_cleanup="false"
                shift
                ;;
            --keep-audio)
                cleanup_audio="false"
                shift
                ;;
            --clean-transcripts)
                keep_transcripts="false"
                shift
                ;;
            --cleanup-delay)
                cleanup_delay=$2
                shift 2
                ;;
            --cache)
                use_cache="true"
                shift
                ;;
            --no-cache)
                use_cache="false"
                shift
                ;;
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
    
    # Seleccionar perfil de compose según el modo
    local compose_profile=""
    case $mode in
        "cpu")
            compose_profile=""
            ;;
        "gpu")
            compose_profile="--profile gpu"
            ;;
        "cache")
            compose_profile="--profile cache"
            ;;
        *)
            echo -e "${RED}Error: Modo no válido: $mode${NC}"
            echo "Modos válidos: cpu, gpu, cache"
            exit 1
            ;;
    esac
    
    # Construir comando base
    local cmd="docker compose $compose_profile run --rm audio-to-text python main.py --start-date $start_date --end-date $end_date"
    
    # Agregar variables de entorno según el modo
    case $mode in
        "cpu")
            cmd="CPU_OPTIMIZED=true MAX_CPU_WORKERS=$workers CHUNK_SIZE=$chunk_size WHISPER_MODEL=$model AUTO_CLEANUP=$auto_cleanup CLEANUP_AUDIO_FILES=$cleanup_audio CLEANUP_TEMP_FILES=$cleanup_temp KEEP_TRANSCRIPTS=$keep_transcripts CLEANUP_DELAY=$cleanup_delay $cmd"
            ;;
        "gpu")
            cmd="GPU_OPTIMIZED=true WHISPER_MODEL=$model AUTO_CLEANUP=$auto_cleanup CLEANUP_AUDIO_FILES=$cleanup_audio CLEANUP_TEMP_FILES=$cleanup_temp KEEP_TRANSCRIPTS=$keep_transcripts CLEANUP_DELAY=$cleanup_delay $cmd"
            ;;
        "cache")
            cmd="WHISPER_MODEL=$model AUTO_CLEANUP=$auto_cleanup CLEANUP_AUDIO_FILES=$cleanup_audio CLEANUP_TEMP_FILES=$cleanup_temp KEEP_TRANSCRIPTS=$keep_transcripts CLEANUP_DELAY=$cleanup_delay $cmd"
            ;;
    esac
    
    echo "$cmd"
}

# Función para verificar Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker no está instalado${NC}"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose no está instalado${NC}"
        exit 1
    fi
}

# Función para verificar archivo .env
check_env() {
    if [[ ! -f .env ]]; then
        echo -e "${YELLOW}Advertencia: No se encontró archivo .env${NC}"
        echo "Copiando env.example a .env..."
        cp env.example .env
        echo -e "${YELLOW}Por favor, edita .env con tu configuración antes de continuar${NC}"
        exit 1
    fi
}

# Función para mostrar estado de servicios
show_status() {
    echo -e "${BLUE}📊 Estado de Servicios:${NC}"
    echo ""
    
    # Verificar servicios estándar (CPU)
    echo -e "${CYAN}Servicios estándar (CPU):${NC}"
    docker compose ps 2>/dev/null || echo "No hay servicios estándar ejecutándose"
    
    # Verificar servicios de GPU
    echo -e "${CYAN}Servicios de GPU:${NC}"
    docker compose --profile gpu ps 2>/dev/null || echo "No hay servicios de GPU ejecutándose"
    
    # Verificar servicios de cache
    echo -e "${CYAN}Servicios de cache:${NC}"
    docker compose --profile cache ps 2>/dev/null || echo "No hay servicios de cache ejecutándose"
}

# Función para detener servicios
stop_services() {
    echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
    
    # Detener servicios estándar (CPU)
    docker compose down 2>/dev/null || true
    
    # Detener servicios de GPU
    docker compose --profile gpu down 2>/dev/null || true
    
    # Detener servicios de cache
    docker compose --profile cache down 2>/dev/null || true
    
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
}

# Función para mostrar logs
show_logs() {
    echo -e "${YELLOW}📋 Mostrando logs en tiempo real...${NC}"
    
    # Mostrar logs de servicios estándar (CPU)
    if docker compose ps -q | grep -q .; then
        echo -e "${CYAN}Logs de servicios estándar (CPU):${NC}"
        docker compose logs -f
    elif docker compose --profile gpu ps -q | grep -q .; then
        echo -e "${CYAN}Logs de servicios GPU:${NC}"
        docker compose --profile gpu logs -f
    elif docker compose --profile cache ps -q | grep -q .; then
        echo -e "${CYAN}Logs de servicios de cache:${NC}"
        docker compose --profile cache logs -f
    else
        echo -e "${YELLOW}No hay servicios ejecutándose${NC}"
    fi
}

# Función para verificar uso de disco
check_disk_usage() {
    echo -e "${YELLOW}💾 Verificando uso de disco...${NC}"
    docker compose run --rm audio-to-text python check_disk_usage.py --detailed
}

# Función para procesar audios
process_audios() {
    local start_date=$1
    local end_date=$2
    shift 2
    
    echo -e "${GREEN}🚀 Procesando audios...${NC}"
    echo -e "${BLUE}📅 Período: $start_date a $end_date${NC}"
    
    # Construir comando
    local command=$(build_command "$start_date" "$end_date" "$@")
    
    echo -e "${BLUE}🔧 Comando: $command${NC}"
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
}

# Función para iniciar servicios y procesar
start_services() {
    local start_date=$1
    local end_date=$2
    shift 2
    
    # Detectar modo
    local mode="cpu"
    for arg in "$@"; do
        if [[ $arg == "--mode" ]]; then
            mode="cpu"  # Valor por defecto
        elif [[ $arg == "--mode"* ]]; then
            mode="${arg#--mode=}"
        fi
    done
    
    echo -e "${GREEN}🚀 Iniciando servicios y procesando audios...${NC}"
    echo -e "${BLUE}📅 Período: $start_date a $end_date${NC}"
    echo -e "${BLUE}⚙️  Modo: $mode${NC}"
    
    # Seleccionar perfil de compose
    local compose_profile=""
    case $mode in
        "cpu")
            compose_profile=""
            ;;
        "gpu")
            compose_profile="--profile gpu"
            ;;
        "cache")
            compose_profile="--profile cache"
            ;;
    esac
    
    # Iniciar servicios
    echo -e "${YELLOW}Iniciando servicios...${NC}"
    docker compose $compose_profile up -d --build
    
    # Procesar audios
    local command=$(build_command "$start_date" "$end_date" "$@")
    echo -e "${BLUE}🔧 Comando: $command${NC}"
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
}

# Verificar Docker
check_docker

# Procesar argumentos
if [[ $# -eq 0 ]] || [[ $1 == "--help" ]] || [[ $1 == "help" ]]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    process)
        if [[ $# -lt 2 ]]; then
            echo -e "${RED}Error: 'process' requiere fecha de inicio y fecha de fin${NC}"
            show_help
            exit 1
        fi
        start_date=$1
        end_date=$2
        shift 2
        if ! validate_date "$start_date" || ! validate_date "$end_date"; then
            exit 1
        fi
        check_env
        process_audios "$start_date" "$end_date" "$@"
        ;;
    start)
        if [[ $# -lt 2 ]]; then
            echo -e "${RED}Error: 'start' requiere fecha de inicio y fecha de fin${NC}"
            show_help
            exit 1
        fi
        start_date=$1
        end_date=$2
        shift 2
        if ! validate_date "$start_date" || ! validate_date "$end_date"; then
            exit 1
        fi
        check_env
        start_services "$start_date" "$end_date" "$@"
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    disk-usage)
        check_disk_usage
        ;;
    *)
        echo -e "${RED}Comando desconocido: $COMMAND${NC}"
        show_help
        exit 1
        ;;
esac
