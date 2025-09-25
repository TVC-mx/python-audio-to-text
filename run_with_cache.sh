#!/bin/bash

# Script para ejecutar con cache del modelo Whisper
# Evita recargar el modelo en cada ejecución

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
SERVICE_PID_FILE="/tmp/whisper_service.pid"
SERVICE_LOG_FILE="/tmp/whisper_service.log"
MODEL_NAME="${WHISPER_MODEL:-base}"

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Procesador de Audio a Texto con Cache de Modelo${NC}"
    echo ""
    echo "Uso: $0 [comando] [argumentos...]"
    echo ""
    echo "Comandos:"
    echo "  start [fecha_inicio] [fecha_fin]    Iniciar procesamiento con cache"
    echo "  stop                                Detener servicio de cache"
    echo "  status                              Verificar estado del servicio"
    echo "  restart                             Reiniciar servicio de cache"
    echo "  logs                                Mostrar logs del servicio"
    echo "  --help                              Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start 2024-01-01 2024-01-31"
    echo "  $0 start 2024-01-01 2024-01-31 --dry-run"
    echo "  $0 status"
    echo "  $0 stop"
}

# Función para verificar si el servicio está corriendo
is_service_running() {
    if [[ -f "$SERVICE_PID_FILE" ]]; then
        local pid=$(cat "$SERVICE_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$SERVICE_PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Función para iniciar el servicio
start_service() {
    if is_service_running; then
        echo -e "${YELLOW}El servicio ya está corriendo${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Iniciando servicio Whisper...${NC}"
    
    # Ejecutar servicio en background
    nohup python3 whisper_service.py --model "$MODEL_NAME" > "$SERVICE_LOG_FILE" 2>&1 &
    local service_pid=$!
    
    # Guardar PID
    echo "$service_pid" > "$SERVICE_PID_FILE"
    
    # Esperar un momento para que el servicio se inicie
    sleep 3
    
    if is_service_running; then
        echo -e "${GREEN}Servicio iniciado exitosamente (PID: $service_pid)${NC}"
        return 0
    else
        echo -e "${RED}Error iniciando servicio${NC}"
        return 1
    fi
}

# Función para detener el servicio
stop_service() {
    if ! is_service_running; then
        echo -e "${YELLOW}El servicio no está corriendo${NC}"
        return 0
    fi
    
    local pid=$(cat "$SERVICE_PID_FILE")
    echo -e "${BLUE}Deteniendo servicio Whisper (PID: $pid)...${NC}"
    
    # Enviar señal de terminación
    kill -TERM "$pid" 2>/dev/null || true
    
    # Esperar a que termine
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done
    
    # Forzar terminación si es necesario
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}Forzando terminación del servicio...${NC}"
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    # Limpiar archivos
    rm -f "$SERVICE_PID_FILE"
    
    echo -e "${GREEN}Servicio detenido${NC}"
}

# Función para verificar estado
check_status() {
    if is_service_running; then
        local pid=$(cat "$SERVICE_PID_FILE")
        echo -e "${GREEN}Servicio corriendo (PID: $pid)${NC}"
        echo -e "${BLUE}Modelo: $MODEL_NAME${NC}"
        return 0
    else
        echo -e "${RED}Servicio no está corriendo${NC}"
        return 1
    fi
}

# Función para mostrar logs
show_logs() {
    if [[ -f "$SERVICE_LOG_FILE" ]]; then
        echo -e "${BLUE}Logs del servicio:${NC}"
        tail -f "$SERVICE_LOG_FILE"
    else
        echo -e "${YELLOW}No hay logs disponibles${NC}"
    fi
}

# Función para ejecutar procesamiento con cache
run_processing() {
    if ! is_service_running; then
        echo -e "${YELLOW}Servicio no está corriendo. Iniciando...${NC}"
        if ! start_service; then
            echo -e "${RED}No se pudo iniciar el servicio${NC}"
            exit 1
        fi
    fi
    
    # Ejecutar procesamiento normal
    echo -e "${GREEN}Ejecutando procesamiento con cache del modelo...${NC}"
    
    # Construir comando original
    local cmd="docker compose run --rm audio-to-text python main.py"
    for arg in "$@"; do
        cmd="$cmd $arg"
    done
    
    echo -e "${BLUE}Comando: $cmd${NC}"
    eval $cmd
}

# Procesar argumentos
if [[ $# -eq 0 ]] || [[ $1 == "--help" ]]; then
    show_help
    exit 0
fi

case "$1" in
    start)
        shift
        if ! is_service_running; then
            start_service
        fi
        run_processing "$@"
        ;;
    stop)
        stop_service
        ;;
    status)
        check_status
        ;;
    restart)
        stop_service
        sleep 2
        start_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo -e "${RED}Comando desconocido: $1${NC}"
        show_help
        exit 1
        ;;
esac
