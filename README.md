# 🎵 Procesador de Audio a Texto - Sistema Unificado

Sistema completo en Docker para procesar llamadas de audio desde MySQL y convertirlas a texto usando Whisper, con soporte para CPU, GPU y cache persistente.

## 🚀 Inicio Rápido

```bash
# 1. Configurar
cp env.example .env
# Editar .env con tu configuración MySQL

# 2. Procesar audios (modo CPU por defecto)
./script.sh process 2024-01-01 2024-01-31

# 3. Procesar con GPU
./script.sh process 2024-01-01 2024-01-31 --mode gpu --model base

# 4. Procesar con cache persistente
./script.sh process 2024-01-01 2024-01-31 --mode cache --model small
```

## ✨ Características Principales

- ✅ **Sistema Unificado**: Un solo script para todas las opciones
- ✅ **Múltiples Modos**: CPU, GPU y Cache persistente
- ✅ **Procesamiento Paralelo**: Workers configurables
- ✅ **Limpieza Automática**: Optimización de espacio en disco
- ✅ **Transcripción Avanzada**: Whisper con múltiples modelos
- ✅ **Logging Estructurado**: Logs con colores y emojis
- ✅ **Monitoreo Integrado**: Estado, logs y uso de disco
- ✅ **Configuración Flexible**: Variables de entorno granulares

## 📁 Estructura del Proyecto

```
python-audio-to-text/
├── script.sh              # Script unificado principal
├── docker-compose.yml     # Docker Compose con perfiles
├── env.example           # Configuración unificada
├── audio_processor.py    # Procesamiento de audio y transcripción
├── database.py           # Gestión de conexión MySQL
├── main.py              # Script principal
├── config.py            # Configuración centralizada
├── check_disk_usage.py  # Utilidad de monitoreo de disco
├── requirements.txt     # Dependencias de Python
├── Dockerfile          # Imagen Docker estándar
├── Dockerfile.gpu      # Imagen Docker para GPU
├── UNIFIED_GUIDE.md    # Guía completa del sistema
└── README.md          # Este archivo
```

## 🎯 Modos de Procesamiento

### **1. Modo CPU (Por defecto)**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode cpu --workers 4 --model tiny
```
- **Optimizado para**: Sistemas sin GPU
- **Características**: Procesamiento paralelo en CPU
- **Recomendado para**: Sistemas básicos a medios

### **2. Modo GPU**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode gpu --model base
```
- **Optimizado para**: Sistemas con GPU NVIDIA
- **Características**: Aceleración por GPU
- **Recomendado para**: Sistemas potentes con GPU

### **3. Modo Cache**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode cache --model small
```
- **Optimizado para**: Procesamiento masivo
- **Características**: Modelo persistente en memoria
- **Recomendado para**: Procesamiento de grandes volúmenes

## 🧹 Limpieza Automática

### **Opciones de Limpieza:**
```bash
# Limpieza automática (por defecto)
./script.sh process 2024-01-01 2024-01-31 --cleanup

# Deshabilitar limpieza
./script.sh process 2024-01-01 2024-01-31 --no-cleanup

# Mantener archivos de audio
./script.sh process 2024-01-01 2024-01-31 --keep-audio

# Limpiar también transcripciones
./script.sh process 2024-01-01 2024-01-31 --clean-transcripts
```

## 📊 Monitoreo y Gestión

### **Comandos de Gestión:**
```bash
# Ver estado de servicios
./script.sh status

# Detener todos los servicios
./script.sh stop

# Ver logs en tiempo real
./script.sh logs

# Verificar uso de disco
./script.sh disk-usage
```

## ⚙️ Configuración

### **Configuración Inicial:**
```bash
# Copiar configuración unificada
cp env.example .env

# Editar configuración
nano .env
```

### **Variables de Entorno Principales:**
```bash
# Base de datos
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=llamadas

# Whisper
WHISPER_MODEL=tiny

# Procesamiento
MAX_CPU_WORKERS=4
CHUNK_SIZE=5

# Limpieza automática
AUTO_CLEANUP=true
CLEANUP_AUDIO_FILES=true
KEEP_TRANSCRIPTS=true
```

## 🚀 Ejemplos de Uso

### **Configuración Básica:**
```bash
# Procesamiento simple
./script.sh process 2024-01-01 2024-01-31

# Con limpieza automática
./script.sh process 2024-01-01 2024-01-31 --cleanup
```

### **Configuración Avanzada:**
```bash
# GPU con modelo grande
./script.sh process 2024-01-01 2024-01-31 --mode gpu --model large

# Cache con limpieza agresiva
./script.sh process 2024-01-01 2024-01-31 --mode cache --clean-transcripts

# CPU optimizado para sistemas potentes
./script.sh process 2024-01-01 2024-01-31 --mode cpu --workers 8 --chunk-size 10
```

### **Configuración de Producción:**
```bash
# Iniciar servicios persistentes
./script.sh start 2024-01-01 2024-01-31 --mode cache --model base

# Monitorear progreso
./script.sh logs

# Verificar uso de disco
./script.sh disk-usage

# Detener servicios
./script.sh stop
```

## 📚 Comandos de Referencia

### **Comandos Principales:**
```bash
./script.sh process [fecha_inicio] [fecha_fin] [opciones]
./script.sh start [fecha_inicio] [fecha_fin] [opciones]
./script.sh stop
./script.sh status
./script.sh logs
./script.sh disk-usage
./script.sh help
```

### **Opciones de Procesamiento:**
```bash
--mode cpu|gpu|cache
--workers N
--chunk-size N
--model tiny|base|small|medium|large
```

### **Opciones de Limpieza:**
```bash
--cleanup
--no-cleanup
--keep-audio
--clean-transcripts
--cleanup-delay N
```

### **Opciones de Salida:**
```bash
--dry-run
--json
--query "SQL"
--build
--logs
```

## 🛠️ Solución de Problemas

### **Problemas Comunes:**

#### **1. Error de Docker:**
```bash
# Verificar Docker
docker --version
docker compose --version

# Reiniciar servicios
./script.sh stop
./script.sh start 2024-01-01 2024-01-31
```

#### **2. Error de GPU:**
```bash
# Verificar GPU
nvidia-smi

# Usar modo CPU
./script.sh process 2024-01-01 2024-01-31 --mode cpu
```

#### **3. Error de Memoria:**
```bash
# Reducir workers
./script.sh process 2024-01-01 2024-01-31 --workers 2

# Reducir chunk size
./script.sh process 2024-01-01 2024-01-31 --chunk-size 3
```

#### **4. Error de Disco:**
```bash
# Verificar uso de disco
./script.sh disk-usage

# Habilitar limpieza automática
./script.sh process 2024-01-01 2024-01-31 --cleanup
```

## 📈 Rendimiento Esperado

### **Procesamiento Paralelo:**
| Método | 10 Llamadas | 50 Llamadas | 100 Llamadas |
|--------|-------------|-------------|--------------|
| **Secuencial** | 15 min | 75 min | 150 min |
| **Paralelo (4 workers)** | 4 min | 20 min | 40 min |
| **Paralelo (6 workers)** | 3 min | 15 min | 30 min |

### **Modelos de Whisper:**
| Modelo | Velocidad | Precisión | Memoria | Recomendado para |
|--------|-----------|-----------|---------|------------------|
| **tiny** | ⚡⚡⚡ | ⭐⭐ | 1GB | CPU básico |
| **base** | ⚡⚡ | ⭐⭐⭐ | 2GB | CPU medio |
| **small** | ⚡ | ⭐⭐⭐⭐ | 3GB | CPU potente |
| **medium** | 🐌 | ⭐⭐⭐⭐⭐ | 5GB | GPU |
| **large** | 🐌🐌 | ⭐⭐⭐⭐⭐ | 10GB | GPU potente |

## 🎯 Mejores Prácticas

### **1. Configuración Inicial:**
```bash
# Copiar configuración
cp env.example .env

# Editar configuración
nano .env

# Probar con modo CPU
./script.sh process 2024-01-01 2024-01-31 --dry-run
```

### **2. Configuración por Sistema:**

#### **Sistema Básico (2-4 cores, 4GB RAM):**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode cpu --workers 2 --model tiny
```

#### **Sistema Medio (4-6 cores, 8GB RAM):**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode cpu --workers 4 --model base
```

#### **Sistema Potente (8+ cores, 16GB RAM):**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode cpu --workers 6 --model small
```

#### **Sistema con GPU:**
```bash
./script.sh process 2024-01-01 2024-01-31 --mode gpu --model base
```

### **3. Configuración de Producción:**
```bash
# Usar cache para grandes volúmenes
./script.sh start 2024-01-01 2024-01-31 --mode cache --model base

# Monitorear progreso
./script.sh logs

# Verificar uso de disco
./script.sh disk-usage
```

## 📖 Documentación Adicional

- **UNIFIED_GUIDE.md**: Guía completa del sistema unificado
- **script.sh --help**: Ayuda del script principal
- **env.example**: Configuración de ejemplo

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte y preguntas:
- Crear un issue en GitHub
- Revisar la documentación en `UNIFIED_GUIDE.md`
- Usar `./script.sh help` para ver todas las opciones