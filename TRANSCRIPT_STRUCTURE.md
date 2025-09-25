# 📁 Nueva Estructura de Transcripciones

## 🎯 Mejoras Implementadas

### **Antes:**
```
./textos/2024/01/15/customer_very_long_filename_with_parameters.mp3?record_id=123456.txt
```

### **Ahora:**
```
./textos/2024/01/15/call_123456/
├── customer_audio123.txt
├── agent_audio123.txt
└── call_metadata.json
```

## 📊 Estructura de Directorios

### **Organización por Llamada:**
```
./textos/
├── 2024/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── call_123456/
│   │   │   │   ├── customer_audio123.txt
│   │   │   │   ├── agent_audio123.txt
│   │   │   │   └── call_metadata.json
│   │   │   ├── call_123457/
│   │   │   │   ├── customer_audio124.txt
│   │   │   │   └── call_metadata.json
│   │   │   └── ...
│   │   └── 16/
│   └── 02/
└── 2025/
```

## 🔧 Características de la Nueva Estructura

### **1. Directorios por Llamada**
- **Formato**: `call_{call_id}`
- **Beneficio**: Cada llamada tiene su propio directorio
- **Ventaja**: Evita conflictos de nombres de archivo

### **2. Nombres de Archivo Truncados**
- **Límite**: 30 caracteres máximo
- **Formato**: `{user_type}_{truncated_name}.txt`
- **Ejemplo**: `customer_audio123.txt` en lugar de `customer_very_long_filename_with_parameters.mp3?record_id=123456.txt`

### **3. Archivo de Metadatos**
- **Archivo**: `call_metadata.json`
- **Contenido**: Información completa de la llamada
- **Beneficio**: Fácil identificación y búsqueda

## 📄 Contenido del Archivo de Metadatos

```json
{
  "call_id": "123456",
  "user_type": "customer",
  "fecha_llamada": "2024-01-15T10:30:00Z",
  "audio_path": "/app/audios/2024/01/15/call_123456/customer_audio123.mp3",
  "transcript_path": "/app/textos/2024/01/15/call_123456/customer_audio123.txt",
  "processed_at": "2024-01-15T10:35:00.123456",
  "original_audio_url": "https://example.com/audio123.mp3?record_id=123456",
  "agent_id": "agent_789",
  "transcript_length": 1234,
  "audio_duration": "unknown"
}
```

## 🛠️ Utilidades de Navegación

### **Script de Búsqueda:**
```bash
# Buscar transcripciones por fecha
python3 find_transcripts.py --date 2024-01-15

# Buscar transcripción por ID de llamada
python3 find_transcripts.py --call-id 123456

# Mostrar contenido de transcripción
python3 find_transcripts.py --show-content 123456

# Mostrar transcripciones recientes
python3 find_transcripts.py --recent 7
```

### **Navegación Manual:**
```bash
# Ver estructura de directorios
ls -la ./textos/2024/01/15/

# Ver contenido de una llamada específica
ls -la ./textos/2024/01/15/call_123456/

# Ver metadatos de una llamada
cat ./textos/2024/01/15/call_123456/call_metadata.json

# Ver transcripción
cat ./textos/2024/01/15/call_123456/customer_audio123.txt
```

## 🎯 Beneficios de la Nueva Estructura

### **1. Organización Mejorada**
- ✅ **Directorio por llamada**: Fácil identificación
- ✅ **Nombres cortos**: Evita problemas de longitud
- ✅ **Metadatos incluidos**: Información completa disponible

### **2. Evita Duplicados**
- ✅ **IDs únicos**: Cada llamada tiene su directorio
- ✅ **Nombres limpios**: Sin parámetros de URL
- ✅ **Estructura consistente**: Fácil navegación

### **3. Mejor Mantenimiento**
- ✅ **Búsqueda fácil**: Por fecha, ID o contenido
- ✅ **Metadatos ricos**: Información completa de cada llamada
- ✅ **Escalabilidad**: Estructura que crece ordenadamente

## 📊 Comparación de Estructuras

| Aspecto | Estructura Anterior | Nueva Estructura |
|---------|-------------------|------------------|
| **Organización** | Por fecha únicamente | Por fecha + llamada |
| **Nombres de archivo** | Muy largos | Truncados (30 chars) |
| **Duplicados** | Posibles | Evitados |
| **Metadatos** | No disponibles | Incluidos |
| **Navegación** | Difícil | Fácil |
| **Búsqueda** | Manual | Automatizada |

## 🔍 Ejemplos de Uso

### **Buscar Transcripción por Fecha:**
```bash
python3 find_transcripts.py --date 2024-01-15
```

### **Encontrar Llamada Específica:**
```bash
python3 find_transcripts.py --call-id 123456
```

### **Ver Contenido de Transcripción:**
```bash
python3 find_transcripts.py --show-content 123456
```

### **Listar Transcripciones Recientes:**
```bash
python3 find_transcripts.py --recent 7
```

## 💡 Notas Importantes

- **Compatibilidad**: La nueva estructura es compatible con el sistema existente
- **Migración**: No se requieren cambios en el código de procesamiento
- **Metadatos**: Se crean automáticamente para cada llamada procesada
- **Búsqueda**: El script de utilidades facilita la navegación y búsqueda

Esta nueva estructura hace que el sistema sea mucho más organizado, escalable y fácil de mantener.
