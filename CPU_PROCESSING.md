# 🖥️ Procesamiento Paralelo en CPU (Sin GPU)

## 🎯 Optimización para CPU

Este documento explica cómo procesar múltiples llamadas en paralelo usando solo CPU, sin necesidad de GPU.

## 🚀 Configuración Rápida

### **1. Usar Script Optimizado para CPU:**
```bash
# Configuración automática para CPU
./run_cpu.sh 2024-01-01 2024-01-31

# Con configuración personalizada
./run_cpu.sh 2024-01-01 2024-01-31 --workers 6 --chunk-size 3 --model tiny
```

### **2. Configuración Manual:**
```bash
# Copiar configuración para CPU
cp env.cpu.example .env

# Editar configuración
nano .env

# Ejecutar con Docker Compose para CPU
docker compose -f docker-compose.cpu.yml up
```

## ⚙️ Configuración de Procesamiento Paralelo

### **Variables de Entorno para CPU:**

```bash
# Configuración optimizada para CPU
CPU_OPTIMIZED=true
MAX_CPU_WORKERS=4
CHUNK_SIZE=5

# Modelo optimizado para CPU
WHISPER_MODEL=tiny

# Procesamiento paralelo
MAX_CONCURRENT_DOWNLOADS=5
MAX_CONCURRENT_TRANSCRIPTIONS=4
```

### **Configuraciones Recomendadas por Tipo de Sistema:**

| Sistema | Workers | Chunk Size | Modelo | Memoria |
|---------|---------|------------|--------|---------|
| **CPU Básico** (2-4 cores) | 2-3 | 3-5 | tiny | 4G |
| **CPU Medio** (4-6 cores) | 4-5 | 5-8 | tiny/base | 6-8G |
| **CPU Potente** (8+ cores) | 6-8 | 8-10 | base/small | 8-12G |

## 🔧 Opciones de Configuración

### **1. Número de Workers:**
```bash
# Para CPU con 4 cores
./run_cpu.sh 2024-01-01 2024-01-31 --workers 4

# Para CPU con 8 cores
./run_cpu.sh 2024-01-01 2024-01-31 --workers 6
```

### **2. Tamaño de Chunk:**
```bash
# Para sistemas con poca memoria
./run_cpu.sh 2024-01-01 2024-01-31 --chunk-size 3

# Para sistemas con mucha memoria
./run_cpu.sh 2024-01-01 2024-01-31 --chunk-size 8
```

### **3. Modelo de Whisper:**
```bash
# Modelo más rápido (recomendado para CPU)
./run_cpu.sh 2024-01-01 2024-01-31 --model tiny

# Modelo balanceado
./run_cpu.sh 2024-01-01 2024-01-31 --model base

# Modelo más preciso (más lento)
./run_cpu.sh 2024-01-01 2024-01-31 --model small
```

## 📊 Comparación de Rendimiento

### **Procesamiento Secuencial vs Paralelo:**

| Método | 10 Llamadas | 50 Llamadas | 100 Llamadas |
|--------|-------------|-------------|--------------|
| **Secuencial** | 15 min | 75 min | 150 min |
| **Paralelo (4 workers)** | 4 min | 20 min | 40 min |
| **Paralelo (6 workers)** | 3 min | 15 min | 30 min |

### **Modelos de Whisper en CPU:**

| Modelo | Velocidad | Precisión | Memoria | Recomendado para |
|--------|-----------|-----------|---------|------------------|
| **tiny** | ⚡⚡⚡ | ⭐⭐ | 1GB | CPU básico |
| **base** | ⚡⚡ | ⭐⭐⭐ | 2GB | CPU medio |
| **small** | ⚡ | ⭐⭐⭐⭐ | 3GB | CPU potente |

## 🛠️ Estrategias de Optimización

### **1. Procesamiento en Chunks:**
- **Ventaja**: Evita sobrecarga de memoria
- **Configuración**: `CHUNK_SIZE=5`
- **Uso**: Automático cuando hay muchas llamadas

### **2. Workers Paralelos:**
- **Ventaja**: Aprovecha múltiples cores de CPU
- **Configuración**: `MAX_CPU_WORKERS=4`
- **Recomendación**: 1 worker por core de CPU

### **3. Descarga Paralela:**
- **Ventaja**: Descarga múltiples audios simultáneamente
- **Configuración**: `MAX_CONCURRENT_DOWNLOADS=5`
- **Recomendación**: 3-5 descargas paralelas

## 📈 Monitoreo de Rendimiento

### **Verificar Uso de CPU:**
```bash
# Monitorear uso de CPU
htop

# Ver procesos de Docker
docker stats audio-to-text-processor-cpu
```

### **Verificar Uso de Memoria:**
```bash
# Ver uso de memoria
free -h

# Ver memoria de contenedor
docker stats --no-stream audio-to-text-processor-cpu
```

### **Logs de Procesamiento:**
```bash
# Ver logs en tiempo real
./run_cpu.sh 2024-01-01 2024-01-31 --logs

# Ver logs del contenedor
docker logs -f audio-to-text-processor-cpu
```

## 🔍 Solución de Problemas

### **Problema: CPU al 100%**
```bash
# Reducir número de workers
./run_cpu.sh 2024-01-01 2024-01-31 --workers 2

# Reducir chunk size
./run_cpu.sh 2024-01-01 2024-01-31 --chunk-size 3
```

### **Problema: Memoria insuficiente**
```bash
# Usar modelo más pequeño
./run_cpu.sh 2024-01-01 2024-01-31 --model tiny

# Reducir chunk size
./run_cpu.sh 2024-01-01 2024-01-31 --chunk-size 2
```

### **Problema: Procesamiento lento**
```bash
# Aumentar workers (si hay cores disponibles)
./run_cpu.sh 2024-01-01 2024-01-31 --workers 6

# Usar modelo más rápido
./run_cpu.sh 2024-01-01 2024-01-31 --model tiny
```

## 💡 Mejores Prácticas

### **1. Configuración Inicial:**
```bash
# Empezar con configuración conservadora
./run_cpu.sh 2024-01-01 2024-01-31 --workers 2 --chunk-size 3 --model tiny

# Ajustar según rendimiento
./run_cpu.sh 2024-01-01 2024-01-31 --workers 4 --chunk-size 5 --model base
```

### **2. Monitoreo Continuo:**
- Verificar uso de CPU (no debe estar al 100% constantemente)
- Verificar uso de memoria (no debe agotarse)
- Verificar logs para errores

### **3. Optimización Gradual:**
- Empezar con configuración conservadora
- Aumentar workers gradualmente
- Ajustar chunk size según memoria disponible
- Cambiar modelo según precisión requerida

## 🎯 Ejemplos de Uso

### **Sistema Básico (2-4 cores, 4GB RAM):**
```bash
./run_cpu.sh 2024-01-01 2024-01-31 --workers 2 --chunk-size 3 --model tiny
```

### **Sistema Medio (4-6 cores, 8GB RAM):**
```bash
./run_cpu.sh 2024-01-01 2024-01-31 --workers 4 --chunk-size 5 --model base
```

### **Sistema Potente (8+ cores, 16GB RAM):**
```bash
./run_cpu.sh 2024-01-01 2024-01-31 --workers 6 --chunk-size 8 --model small
```

## 📊 Resultados Esperados

Con la configuración optimizada para CPU, puedes esperar:

- **Procesamiento paralelo**: 3-6 llamadas simultáneas
- **Velocidad**: 2-4x más rápido que procesamiento secuencial
- **Eficiencia**: Aprovechamiento óptimo de recursos de CPU
- **Estabilidad**: Procesamiento estable sin sobrecarga

¡El procesamiento paralelo en CPU es muy efectivo y puede procesar múltiples llamadas simultáneamente!
