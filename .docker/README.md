# Docker Services - Audio to Text

Esta carpeta contiene toda la configuración de Docker para el proyecto de transcripción de audio.

## Estructura

```
.docker/
├── docker-compose.yml          # Orquestación de todos los servicios
├── Dockerfile.python          # Imagen de la aplicación Python
├── Dockerfile.whisper         # Imagen del servicio de Whisper
├── whisper_service.py         # Código del servicio de Whisper
├── config.whisper.py          # Configuración del servicio de Whisper
├── requirements.whisper.txt   # Dependencias del servicio de Whisper
├── start-services.sh          # Script para iniciar todos los servicios
├── run-python-app.sh          # Script para ejecutar la app Python
└── env.example                # Variables de entorno de ejemplo
```

## Servicios

### 1. whisper-service
- **Puerto**: 8000
- **Función**: Servicio independiente de transcripción con Whisper
- **Modelo**: Persistente en volumen Docker
- **API**: REST con FastAPI

### 2. python-app
- **Función**: Aplicación principal de Python
- **Dependencias**: Requiere que whisper-service esté saludable
- **Comunicación**: HTTP con whisper-service

## Uso Rápido

### Iniciar todos los servicios
```bash
cd .docker
./start-services.sh
```

### Ejecutar la aplicación Python
```bash
cd .docker
./run-python-app.sh --start-date 2024-01-01 --end-date 2024-01-02
```

### Ver logs
```bash
cd .docker
docker-compose logs -f                    # Todos los servicios
docker-compose logs -f whisper-service    # Solo Whisper
docker-compose logs -f python-app         # Solo Python
```

### Detener servicios
```bash
cd .docker
docker-compose down
```

## Configuración

### Variables de Entorno
Copia `env.example` a `.env` y configura:

```bash
cp env.example .env
# Editar .env con tus valores
```

### Modelo de Whisper
Cambiar el modelo en `docker-compose.yml`:
```yaml
environment:
  - WHISPER_MODEL=medium  # tiny, base, small, medium, large
```

## Ventajas de esta Arquitectura

- ✅ **Modelo persistente**: No se re-descarga al cambiar código
- ✅ **Servicios independientes**: Whisper y Python separados
- ✅ **Escalabilidad**: Múltiples instancias de Python pueden usar el mismo Whisper
- ✅ **Desarrollo ágil**: Cambios de código sin tocar el modelo
- ✅ **Gestión simplificada**: Un solo docker-compose

## Comandos Útiles

### Reconstruir solo el servicio de Whisper
```bash
docker-compose build whisper-service
docker-compose up -d whisper-service
```

### Reconstruir solo la aplicación Python
```bash
docker-compose build python-app
docker-compose up -d python-app
```

### Ver estado de los servicios
```bash
docker-compose ps
```

### Acceder al contenedor de Python
```bash
docker-compose exec python-app bash
```

### Acceder al contenedor de Whisper
```bash
docker-compose exec whisper-service bash
```

### Limpiar volúmenes (eliminar modelo)
```bash
docker-compose down -v
```

## Troubleshooting

### El servicio de Whisper no inicia
```bash
# Ver logs
docker-compose logs whisper-service

# Verificar recursos
docker stats
```

### La aplicación Python no se conecta
```bash
# Verificar que Whisper esté saludable
curl http://localhost:8000/health

# Ver logs de Python
docker-compose logs python-app
```

### Problemas de memoria
- Usar modelo más pequeño (`medium` en lugar de `large`)
- Reducir `MAX_CPU_WORKERS`
- Aumentar memoria del contenedor

## Desarrollo

### Modificar código Python
1. Los cambios se reflejan automáticamente
2. No necesitas reconstruir el servicio de Whisper

### Modificar servicio de Whisper
1. Reconstruir: `docker-compose build whisper-service`
2. Reiniciar: `docker-compose up -d whisper-service`

### Actualizar modelo de Whisper
1. Cambiar `WHISPER_MODEL` en docker-compose.yml
2. Eliminar volumen: `docker-compose down -v`
3. Reiniciar: `./start-services.sh`
