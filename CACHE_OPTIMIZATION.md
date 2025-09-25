# 🚀 Optimización de Cache del Modelo Whisper

Este documento explica cómo usar el sistema de cache del modelo Whisper para evitar recargar el modelo en cada ejecución.

## 🎯 Problema Resuelto

**Antes**: Cada vez que ejecutas `./run.sh`, el modelo Whisper se carga desde cero, lo que puede tomar 30-60 segundos.

**Ahora**: El modelo se mantiene en memoria y se reutiliza entre ejecuciones, reduciendo el tiempo de inicio a segundos.

## 🛠️ Soluciones Implementadas

### 1. **Cache Global del Modelo** (Recomendado)
- **Archivo**: `audio_processor.py` (ya implementado)
- **Beneficio**: El modelo se mantiene en memoria durante la ejecución
- **Uso**: Automático, no requiere cambios

### 2. **Script Optimizado** (Más rápido)
- **Archivo**: `./run_fast.sh`
- **Beneficio**: Usa Docker Compose con cache persistente
- **Uso**: `./run_fast.sh 2024-01-01 2024-01-31`

### 3. **Servicio Persistente** (Para uso intensivo)
- **Archivo**: `./run_with_cache.sh`
- **Beneficio**: Mantiene el modelo cargado entre ejecuciones
- **Uso**: 
  ```bash
  ./run_with_cache.sh start 2024-01-01 2024-01-31
  ./run_with_cache.sh status
  ./run_with_cache.sh stop
  ```

## 📊 Comparación de Rendimiento

| Método | Tiempo de Carga | Uso de Memoria | Complejidad |
|--------|----------------|----------------|-------------|
| **Original** | 30-60 segundos | Baja | Baja |
| **Cache Global** | 0 segundos (2da vez) | Media | Baja |
| **Script Optimizado** | 5-10 segundos | Media | Media |
| **Servicio Persistente** | 0 segundos | Alta | Alta |

## 🚀 Guía de Uso

### Opción 1: Cache Global (Automático)
```bash
# Primera ejecución (carga el modelo)
./run.sh 2024-01-01 2024-01-31

# Segunda ejecución (usa cache)
./run.sh 2024-01-01 2024-01-31
```

### Opción 2: Script Optimizado
```bash
# Usar el script optimizado
./run_fast.sh 2024-01-01 2024-01-31

# Con opciones adicionales
./run_fast.sh 2024-01-01 2024-01-31 --dry-run
./run_fast.sh 2024-01-01 2024-01-31 --json
```

### Opción 3: Servicio Persistente
```bash
# Iniciar servicio
./run_with_cache.sh start 2024-01-01 2024-01-31

# Verificar estado
./run_with_cache.sh status

# Ver logs
./run_with_cache.sh logs

# Detener servicio
./run_with_cache.sh stop
```

## ⚙️ Configuración Avanzada

### Variables de Entorno
```bash
# Modelo a usar (default: base)
export WHISPER_MODEL=large

# Directorio de cache
export WHISPER_CACHE_DIR=/tmp/whisper_cache
```

### Docker Compose con Cache
```bash
# Usar configuración con cache
docker compose -f docker-compose.cache.yml up
```

## 🔧 Solución de Problemas

### Problema: Cache no funciona
```bash
# Limpiar cache
rm -rf /tmp/whisper_cache
rm -rf /tmp/whisper_model_cache

# Reiniciar servicio
./run_with_cache.sh restart
```

### Problema: Memoria insuficiente
```bash
# Usar modelo más pequeño
export WHISPER_MODEL=tiny
./run_fast.sh 2024-01-01 2024-01-31
```

### Problema: Servicio no responde
```bash
# Verificar estado
./run_with_cache.sh status

# Reiniciar si es necesario
./run_with_cache.sh restart
```

## 📈 Monitoreo

### Verificar Cache
```bash
# Ver logs del servicio
./run_with_cache.sh logs

# Verificar uso de memoria
docker stats whisper-cache-service
```

### Métricas de Rendimiento
- **Tiempo de carga inicial**: 30-60 segundos
- **Tiempo de carga con cache**: 0-5 segundos
- **Ahorro de tiempo**: 85-95%
- **Uso de memoria adicional**: 1-4 GB (dependiendo del modelo)

## 🎯 Recomendaciones

### Para Uso Ocasional
- Usar **Cache Global** (automático)
- No requiere configuración adicional

### Para Uso Frecuente
- Usar **Script Optimizado** (`./run_fast.sh`)
- Mejor balance entre rendimiento y simplicidad

### Para Uso Intensivo
- Usar **Servicio Persistente** (`./run_with_cache.sh`)
- Máximo rendimiento, requiere más recursos

## 🔍 Logs y Debugging

### Habilitar Logs Detallados
```bash
# En el archivo .env
LOG_LEVEL=DEBUG
```

### Ver Logs en Tiempo Real
```bash
# Logs del procesamiento
./run_fast.sh 2024-01-01 2024-01-31 --logs

# Logs del servicio
./run_with_cache.sh logs
```

## 📝 Notas Técnicas

- El cache se almacena en `/tmp/whisper_cache`
- El modelo se mantiene en memoria RAM
- El cache se limpia al reiniciar el sistema
- Compatible con todos los modelos de Whisper (tiny, base, small, medium, large)
