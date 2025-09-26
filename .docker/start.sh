#!/bin/bash

# Script unificado para gestionar los servicios de audio-to-text

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [COMANDO] [ARGUMENTOS]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start                    Iniciar todos los servicios"
    echo "  stop                     Detener todos los servicios"
    echo "  restart                  Reiniciar todos los servicios"
    echo "  status                   Mostrar estado de los servicios"
    echo "  logs [servicio]          Mostrar logs (whisper|python|all)"
    echo "  run [args...]            Ejecutar aplicación Python con argumentos"
    echo "  build                    Reconstruir todas las imágenes"
    echo "  clean                    Limpiar volúmenes y contenedores"
    echo "  shell [servicio]         Acceder al shell del servicio"
    echo "  health                   Verificar salud de los servicios"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start                                    # Iniciar servicios"
    echo "  $0 run --start-date 2024-01-01 --end-date 2024-01-02"
    echo "  $0 run --start-date 2024-01-01 --end-date 2024-01-02 --cleanup-audio"
    echo "  $0 run --start-date 2024-01-01 --end-date 2024-01-02 --keep-audio"
    echo "  $0 logs whisper                            # Logs del servicio Whisper"
    echo "  $0 shell python                            # Shell de la app Python"
}

# Función para verificar Docker
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker no está ejecutándose. Por favor, inicia Docker primero.${NC}"
        exit 1
    fi
}

# Función para cambiar al directorio correcto
cd_to_docker() {
    cd "$(dirname "$0")"
}

# Función para iniciar servicios
start_services() {
    echo -e "${BLUE}🚀 Iniciando servicios de audio-to-text...${NC}"
    
    check_docker
    cd_to_docker
    
    # Detener servicios existentes
    echo -e "${YELLOW}🛑 Deteniendo servicios existentes...${NC}"
    docker compose down > /dev/null 2>&1 || true
    
    # Construir imágenes
    echo -e "${YELLOW}🔨 Construyendo imágenes...${NC}"
    docker compose build
    
    # Iniciar servicios
    echo -e "${YELLOW}🚀 Iniciando servicios...${NC}"
    docker compose up -d
    
    # Esperar a que estén listos
    echo -e "${YELLOW}⏳ Esperando a que los servicios estén listos...${NC}"
    sleep 15
    
    # Verificar servicios
    echo -e "${YELLOW}🔍 Verificando servicios...${NC}"
    
    # Verificar Whisper
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Servicio de Whisper iniciado${NC}"
    else
        echo -e "${RED}❌ Servicio de Whisper no responde${NC}"
        docker compose logs whisper-service
        exit 1
    fi
    
    # Verificar Python
    if docker compose ps python-app | grep -q "Up"; then
        echo -e "${GREEN}✅ Aplicación Python iniciada${NC}"
    else
        echo -e "${RED}❌ Aplicación Python no está ejecutándose${NC}"
        docker compose logs python-app
        exit 1
    fi
    
    echo -e "${GREEN}🎉 Todos los servicios están ejecutándose correctamente!${NC}"
    show_status
}

# Función para detener servicios
stop_services() {
    echo -e "${YELLOW}🛑 Deteniendo servicios...${NC}"
    check_docker
    cd_to_docker
    docker compose down
    echo -e "${GREEN}✅ Servicios detenidos${NC}"
}

# Función para reiniciar servicios
restart_services() {
    echo -e "${YELLOW}🔄 Reiniciando servicios...${NC}"
    stop_services
    start_services
}

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado de los servicios:${NC}"
    cd_to_docker
    docker compose ps
    echo ""
    echo -e "${BLUE}📡 URLs:${NC}"
    echo "  - Whisper Service: http://localhost:8000"
    echo "  - Health Check: http://localhost:8000/health"
}

# Función para mostrar logs
show_logs() {
    local service=${1:-all}
    cd_to_docker
    
    case $service in
        whisper)
            echo -e "${BLUE}📋 Logs del servicio Whisper:${NC}"
            docker compose logs -f whisper-service
            ;;
        python)
            echo -e "${BLUE}📋 Logs de la aplicación Python:${NC}"
            docker compose logs -f python-app
            ;;
        all|*)
            echo -e "${BLUE}📋 Logs de todos los servicios:${NC}"
            docker compose logs -f
            ;;
    esac
}

# Función para ejecutar aplicación Python
run_app() {
    echo -e "${BLUE}🐍 Ejecutando aplicación Python: $@${NC}"
    check_docker
    cd_to_docker
    
    # Verificar que los servicios estén ejecutándose
    if ! docker compose ps | grep -q "whisper-service.*Up"; then
        echo -e "${RED}❌ El servicio de Whisper no está ejecutándose${NC}"
        echo -e "${YELLOW}💡 Ejecuta primero: $0 start${NC}"
        exit 1
    fi
    
    docker compose exec python-app python main.py "$@"
}

# Función para reconstruir
build_images() {
    echo -e "${YELLOW}🔨 Reconstruyendo imágenes...${NC}"
    check_docker
    cd_to_docker
    docker compose build --no-cache
    echo -e "${GREEN}✅ Imágenes reconstruidas${NC}"
}

# Función para limpiar
clean_all() {
    echo -e "${YELLOW}🧹 Limpiando volúmenes y contenedores...${NC}"
    check_docker
    cd_to_docker
    docker compose down -v
    docker system prune -f
    echo -e "${GREEN}✅ Limpieza completada${NC}"
}

# Función para acceder al shell
access_shell() {
    local service=${1:-python}
    cd_to_docker
    
    case $service in
        whisper)
            echo -e "${BLUE}🐚 Accediendo al shell del servicio Whisper...${NC}"
            docker compose exec whisper-service bash
            ;;
        python)
            echo -e "${BLUE}🐚 Accediendo al shell de la aplicación Python...${NC}"
            docker compose exec python-app bash
            ;;
        *)
            echo -e "${RED}❌ Servicio no válido. Usa: whisper o python${NC}"
            exit 1
            ;;
    esac
}

# Función para verificar salud
check_health() {
    echo -e "${BLUE}🏥 Verificando salud de los servicios...${NC}"
    cd_to_docker
    
    # Verificar Whisper
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Whisper Service: Saludable${NC}"
        curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
    else
        echo -e "${RED}❌ Whisper Service: No responde${NC}"
    fi
    
    # Verificar Python
    if docker compose ps python-app | grep -q "Up"; then
        echo -e "${GREEN}✅ Python App: Ejecutándose${NC}"
    else
        echo -e "${RED}❌ Python App: No está ejecutándose${NC}"
    fi
}

# Función principal
main() {
    case ${1:-help} in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$2"
            ;;
        run)
            shift
            run_app "$@"
            ;;
        build)
            build_images
            ;;
        clean)
            clean_all
            ;;
        shell)
            access_shell "$2"
            ;;
        health)
            check_health
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ Comando no reconocido: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
