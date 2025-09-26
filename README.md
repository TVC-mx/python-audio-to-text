# Audio to Text - Sistema de Transcripción

Sistema de transcripción de audio a texto usando Whisper con arquitectura de microservicios en Docker.

## 🏗️ Arquitectura

```
┌─────────────────────┐    HTTP API    ┌─────────────────────┐
│   Aplicación Python │ ──────────────► │  Servicio Whisper   │
│   (Cliente)         │                │   (Docker Container) │
└─────────────────────┘                └─────────────────────┘
```

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno
```bash
cp .docker/env.example .docker/.env
# Editar .docker/.env con tus valores
```

### 2. Iniciar Servicios
```bash
cd .docker
./start.sh start
```

### 3. Ejecutar Transcripción
```bash
./start.sh run --start-date 2024-01-01 --end-date 2024-01-02
```

## 📁 Estructura del Proyecto

```
python-audio-to-text/
├── .docker/                    # Configuración Docker
│   ├── docker-compose.yml     # Orquestación de servicios
│   ├── Dockerfile.python      # Imagen de la app Python
│   ├── Dockerfile.whisper     # Imagen del servicio Whisper
│   ├── start.sh               # Script unificado de gestión
│   └── README.md              # Documentación Docker
├── audio_processor_client.py  # Cliente para el servicio Whisper
├── main.py                    # Aplicación principal
├── config.py                  # Configuración
└── requirements.txt           # Dependencias Python
```

## 🛠️ Comandos Disponibles

### Gestión de Servicios
```bash
cd .docker

./start.sh start              # Iniciar todos los servicios
./start.sh stop               # Detener todos los servicios
./start.sh restart            # Reiniciar servicios
./start.sh status             # Ver estado de servicios
./start.sh health             # Verificar salud de servicios
```

### Logs y Debugging
```bash
./start.sh logs               # Logs de todos los servicios
./start.sh logs whisper       # Logs del servicio Whisper
./start.sh logs python        # Logs de la aplicación Python
./start.sh shell python       # Acceder al shell de Python
./start.sh shell whisper      # Acceder al shell de Whisper
```

### Desarrollo
```bash
./start.sh build              # Reconstruir todas las imágenes
./start.sh clean              # Limpiar volúmenes y contenedores
./start.sh run [args...]      # Ejecutar app Python con argumentos
```

## 🔧 Configuración

### Variables de Entorno (.docker/.env)
```bash
# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=llamadas

# Audio
AUDIO_BASE_URL=https://your-audio-server.com

# Whisper
WHISPER_MODEL=large  # tiny, base, small, medium, large

# Procesamiento
MAX_CPU_WORKERS=4
ENABLE_PARALLEL_TRANSCRIPTIONS=true

# Limpieza (por defecto: mantener archivos de audio)
AUTO_CLEANUP=true
CLEANUP_AUDIO_FILES=false  # NO eliminar archivos de audio por defecto
KEEP_TRANSCRIPTS=true
```

## 📊 Servicios

### Servicio de Whisper
- **Puerto**: 8000
- **URL**: http://localhost:8000
- **Health**: http://localhost:8000/health
- **Función**: Transcripción de audio con modelo persistente

### Aplicación Python
- **Función**: Cliente que se conecta al servicio de Whisper
- **Comunicación**: HTTP REST API
- **Dependencias**: Requiere servicio de Whisper saludable

## 🎯 Ventajas de esta Arquitectura

- ✅ **Modelo Persistente**: No se re-descarga al cambiar código
- ✅ **Servicios Independientes**: Whisper y Python separados
- ✅ **Escalabilidad**: Múltiples clientes, un solo modelo
- ✅ **Desarrollo Ágil**: Cambios de código sin tocar el modelo
- ✅ **Gestión Simplificada**: Un solo script para todo

## 🔍 Troubleshooting

### El servicio de Whisper no inicia
```bash
./start.sh logs whisper
./start.sh health
```

### La aplicación Python no se conecta
```bash
./start.sh logs python
curl http://localhost:8000/health
```

### Problemas de memoria
- Cambiar `WHISPER_MODEL=medium` en docker-compose.yml
- Reducir `MAX_CPU_WORKERS`
- Aumentar memoria del contenedor

### Limpiar todo y empezar de nuevo
```bash
./start.sh clean
./start.sh start
```

### Gestión de archivos de audio
```bash
# Por defecto: NO se eliminan archivos de audio (se mantienen)
./start.sh run 2025-01-01 2025-01-31

# Si quieres eliminar archivos de audio después de procesar
./start.sh run 2025-01-01 2025-01-31 --cleanup-audio

# Si quieres mantener archivos de audio (comportamiento por defecto)
./start.sh run 2025-01-01 2025-01-31 --keep-audio
```

## 📈 Escalabilidad

### Múltiples instancias de Python
```yaml
# En docker-compose.yml
services:
  python-app-1:
    # ... configuración
  python-app-2:
    # ... configuración
```

### Cambiar modelo de Whisper
1. Editar `WHISPER_MODEL` en docker-compose.yml
2. `./start.sh clean` (elimina modelo anterior)
3. `./start.sh start` (descarga nuevo modelo)

## 🚀 Desarrollo

### Modificar código Python
- Los cambios se reflejan automáticamente
- No necesitas reconstruir el servicio de Whisper

### Modificar servicio de Whisper
```bash
./start.sh build
./start.sh restart
```

### Ver logs en tiempo real
```bash
./start.sh logs
```

## 📋 Ejemplos de Uso

### Procesar un rango de fechas
```bash
./start.sh run --start-date 2024-01-01 --end-date 2024-01-31
```

### Modo dry-run
```bash
./start.sh run --start-date 2024-01-01 --end-date 2024-01-02 --dry-run
```

### Con query personalizada
```bash
./start.sh run --start-date 2024-01-01 --end-date 2024-01-02 --query "SELECT * FROM calls WHERE user_type = 'customer'"
```

## 🔗 URLs Importantes

- **Servicio Whisper**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs (si está habilitado)

## 📞 Soporte

Para problemas o preguntas:
1. Verificar logs: `./start.sh logs`
2. Verificar salud: `./start.sh health`
3. Revisar configuración en `.docker/.env`
4. Consultar documentación en `.docker/README.md`