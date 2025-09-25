# 🎵 Guía Unificada - Procesador de Audio a Texto

## 🚀 Script Unificado

El sistema ahora usa un solo script `script.sh` que maneja todas las opciones y modos de procesamiento.

### **Uso Básico:**
```bash
# Procesar audios (modo CPU por defecto)
./script.sh process 2024-01-01 2024-01-31

# Procesar con GPU
./script.sh process 2024-01-01 2024-01-31 --mode gpu --model base

# Procesar con cache persistente
./script.sh process 2024-01-01 2024-01-31 --mode cache --model small

# Iniciar servicios y procesar
./script.sh start 2024-01-01 2024-01-31 --mode cpu --workers 6
```

## ⚙️ Modos de Procesamiento

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

## 🧹 Configuración de Limpieza Automática

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

### **Configuración Granular:**
- ✅ **AUTO_CLEANUP**: Habilitar/deshabilitar limpieza
- ✅ **CLEANUP_AUDIO_FILES**: Limpiar archivos de audio
- ✅ **CLEANUP_TEMP_FILES**: Limpiar archivos temporales
- ✅ **KEEP_TRANSCRIPTS**: Mantener transcripciones
- ✅ **CLEANUP_DELAY**: Delay antes de limpiar

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

### **Información de Estado:**
- 📊 **Servicios CPU**: Estado de procesamiento estándar
- 🎮 **Servicios GPU**: Estado de procesamiento con GPU
- 💾 **Servicios Cache**: Estado de cache persistente

## 🔧 Configuración Avanzada

### **Variables de Entorno (.env):**
```bash
# Copiar configuración
cp env.example .env

# Editar configuración
nano .env
```

### **Configuración por Modo:**

#### **CPU:**
```bash
CPU_OPTIMIZED=true
MAX_CPU_WORKERS=4
CHUNK_SIZE=5
WHISPER_MODEL=tiny
```

#### **GPU:**
```bash
GPU_OPTIMIZED=true
CUDA_VISIBLE_DEVICES=0
WHISPER_MODEL=base
```

#### **Cache:**
```bash
WHISPER_MODEL=small
# Cache se maneja automáticamente
```

## 📈 Ejemplos de Uso

### **Configuración Básica:**
```bash
# Procesamiento simple
./script.sh process 2024-01-01 2024-01-31

# Con limpieza automática
./script.sh process 2024-01-01 2024-01-31 --cleanup

# Con configuración personalizada
./script.sh process 2024-01-01 2024-01-31 --workers 6 --chunk-size 3 --model base
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

# Verificar estado
./script.sh status

# Monitorear logs
./script.sh logs

# Verificar uso de disco
./script.sh disk-usage

# Detener servicios
./script.sh stop
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

¡El sistema unificado simplifica enormemente el uso y mantenimiento!
