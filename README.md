# Procesador de Audio a Texto

Sistema completo en Docker para procesar llamadas de audio desde MySQL y convertirlas a texto usando Whisper.

## 🚀 Inicio Rápido

```bash
# 1. Configurar
cp env.example .env
# Editar .env con tu configuración MySQL

# 2. Construir
docker-compose build

# 3. Probar
./run.sh 2024-01-01 2024-01-31 --dry-run

# 4. Procesar
./run.sh 2024-01-01 2024-01-31
```

## Características

- ✅ Conexión a MySQL para obtener llamadas por rango de fechas
- ✅ Descarga automática de audios organizados por carpetas (año/mes/día)
- ✅ Transcripción usando OpenAI Whisper (librería gratuita)
- ✅ Procesamiento paralelo para mayor eficiencia
- ✅ Prefijos de user_type en archivos
- ✅ Todo ejecutándose en contenedores Docker
- ✅ Logs detallados y reportes

## Estructura del Proyecto

```
python-audio-to-text/
├── Dockerfile              # Imagen Docker con Python y dependencias
├── docker-compose.yml      # Orquestación de contenedores
├── requirements.txt        # Dependencias de Python
├── config.py              # Configuración centralizada
├── database.py            # Gestión de conexión MySQL
├── audio_processor.py     # Procesamiento de audio y transcripción
├── main.py               # Script principal
├── env.example           # Ejemplo de variables de entorno
└── README.md            # Este archivo
```

## Requisitos Previos

- **Docker y Docker Compose** instalados
- **Acceso a MySQL** con las tablas: `calls`, `call_audios`, `branches`, `users`, `persons`
- **URLs de audio accesibles** desde el contenedor Docker
- **4GB de RAM** disponibles para el contenedor (recomendado)

## 🔄 Flujo de Trabajo con Docker

### Paso 1: Configuración
```bash
# Clonar/descargar el proyecto
cd python-audio-to-text

# Configurar variables de entorno
cp env.example .env
nano .env  # Editar con tu configuración MySQL
```

### Paso 2: Construcción
```bash
# Construir la imagen Docker (solo la primera vez o cuando cambies código)
docker-compose build
```

### Paso 3: Prueba
```bash
# Probar conexión a MySQL
docker-compose run --rm audio-to-text \
  python -c "from database import DatabaseManager; db = DatabaseManager(); print('Conexión:', db.test_connection())"

# Modo dry-run para ver qué se procesaría
./run.sh 2024-01-01 2024-01-31 --dry-run
```

### Paso 4: Procesamiento
```bash
# Procesar llamadas reales
./run.sh 2024-01-01 2024-01-31

# O con docker-compose directamente
docker-compose run --rm audio-to-text \
  python main.py --start-date 2024-01-01 --end-date 2024-01-31
```

### Paso 5: Verificación
```bash
# Ver archivos generados
ls -la audios/2024/01/15/
ls -la textos/2024/01/15/

# Ver logs
cat logs/processing.log
```

## Configuración

### 1. Variables de Entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp env.example .env
```

Edita `.env` con tu configuración:

```env
# Configuración de MySQL
MYSQL_HOST=tu-servidor-mysql.com
MYSQL_PORT=3306
MYSQL_USER=tu_usuario
MYSQL_PASSWORD=tu_password
MYSQL_DATABASE=llamadas

# URL base para descargar audios (solo si las URLs en la BD no son completas)
AUDIO_BASE_URL=http://tu-servidor.com/audios

# Modelo de Whisper (base recomendado)
WHISPER_MODEL=base
```

### 2. Estructura de Base de Datos

El sistema está configurado para trabajar con tu esquema de base de datos que incluye las siguientes tablas:

```sql
-- Tabla principal de llamadas
calls (
    id, started_at, ended_at, company_id, branch_id, attended_by_employee_id
)

-- Tabla de audios de llamadas
call_audios (
    call_id, user_type, audio_url
)

-- Tabla de sucursales
branches (
    id, name
)

-- Tabla de usuarios
users (
    id, person_id
)

-- Tabla de personas
persons (
    id, full_name
)
```

**Consulta por defecto:**
```sql
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;
```

**Nota:** El campo `audio_url` debe contener la URL completa del archivo de audio, como:
```
https://tvc-voximplant.sfo3.digitaloceanspaces.com/2025/06/27/archivo.mp3
```

## 🚀 Uso con Docker

### 1. Configuración Inicial

```bash
# 1. Configurar variables de entorno
cp env.example .env
# Editar .env con tu configuración MySQL

# 2. Construir la imagen Docker
docker-compose build
```

### 2. Ejecución Básica

```bash
# Procesar llamadas del 1 al 31 de enero de 2024
docker-compose run --rm audio-to-text \
  python main.py --start-date 2024-01-01 --end-date 2024-01-31
```

### 3. Usando el Script de Ayuda (Recomendado)

```bash
# Hacer ejecutable el script
chmod +x run.sh

# Procesar llamadas
./run.sh 2024-01-01 2024-01-31

# Modo dry-run (solo mostrar qué se procesaría)
./run.sh 2024-01-01 2024-01-31 --dry-run

# Generar reporte en JSON
./run.sh 2024-01-01 2024-01-31 --json

# Reconstruir imagen y procesar
./run.sh 2024-01-01 2024-01-31 --build
```

### 4. Consultas Personalizadas

```bash
# Solo llamadas de clientes
docker-compose run --rm audio-to-text \
  python main.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "SELECT c.id AS id, c.started_at AS fecha_llamada, ca.user_type AS user_type, ca.audio_url AS audio_path FROM calls c LEFT JOIN call_audios ca ON ca.call_id = c.id WHERE DATE(c.started_at) BETWEEN %s AND %s AND ca.user_type = 'cliente' AND ca.audio_url IS NOT NULL"

# Solo llamadas de una sucursal específica
docker-compose run --rm audio-to-text \
  python main.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "SELECT c.id AS id, c.started_at AS fecha_llamada, ca.user_type AS user_type, ca.audio_url AS audio_path FROM calls c LEFT JOIN call_audios ca ON ca.call_id = c.id WHERE DATE(c.started_at) BETWEEN %s AND %s AND c.branch_id = 123 AND ca.audio_url IS NOT NULL"

# Llamadas con duración mínima (más de 30 segundos)
docker-compose run --rm audio-to-text \
  python main.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "SELECT c.id AS id, c.started_at AS fecha_llamada, ca.user_type AS user_type, ca.audio_url AS audio_path FROM calls c LEFT JOIN call_audios ca ON ca.call_id = c.id WHERE DATE(c.started_at) BETWEEN %s AND %s AND TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) > 30 AND ca.audio_url IS NOT NULL"
```

### 5. Verificación y Debugging

```bash
# Probar conexión a MySQL
docker-compose run --rm audio-to-text \
  python -c "from database import DatabaseManager; db = DatabaseManager(); print('Conexión:', db.test_connection())"

# Entrar al contenedor para debugging
docker-compose run --rm audio-to-text bash

# Ver logs en tiempo real
docker-compose logs -f audio-to-text

# Verificar archivos generados
ls -la audios/2024/01/15/
ls -la textos/2024/01/15/
```

### 6. Ejemplos de Uso Común

```bash
# Procesar llamadas de la última semana
./run.sh 2024-01-01 2024-01-07

# Procesar solo llamadas de clientes de un día específico
docker-compose run --rm audio-to-text \
  python main.py \
  --start-date 2024-01-15 \
  --end-date 2024-01-15 \
  --query "SELECT c.id AS id, c.started_at AS fecha_llamada, ca.user_type AS user_type, ca.audio_url AS audio_path FROM calls c LEFT JOIN call_audios ca ON ca.call_id = c.id WHERE DATE(c.started_at) = '2024-01-15' AND ca.user_type = 'cliente' AND ca.audio_url IS NOT NULL"

# Procesar con reporte detallado
./run.sh 2024-01-01 2024-01-31 --json
```

## Estructura de Archivos Generados

### Audios Descargados
```
audios/
├── 2024/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── cliente_llamada_001.wav
│   │   │   └── agente_llamada_002.wav
│   │   └── 16/
│   │       └── supervisor_llamada_003.wav
│   └── 02/
│       └── 01/
│           └── cliente_llamada_004.wav
```

### Transcripciones
```
textos/
├── 2024/
│   ├── 01/
│   │   ├── 15/
│   │   │   ├── cliente_llamada_001.txt
│   │   │   └── agente_llamada_002.txt
│   │   └── 16/
│   │       └── supervisor_llamada_003.txt
│   └── 02/
│       └── 01/
│           └── cliente_llamada_004.txt
```

### Logs
```
logs/
├── processing.log                    # Log general
├── procesamiento_2024-01-01_2024-01-31.log  # Log de resultados
└── reporte_2024-01-01_2024-01-31.json       # Reporte JSON (opcional)
```

## Modelos de Whisper Disponibles

| Modelo  | Tamaño | Velocidad | Precisión | Uso Recomendado |
|---------|--------|-----------|-----------|-----------------|
| tiny    | 39 MB  | Muy rápido| Baja      | Pruebas rápidas |
| base    | 74 MB  | Rápido    | Buena     | **Recomendado** |
| small   | 244 MB | Medio     | Muy buena | Producción      |
| medium  | 769 MB | Lento     | Excelente | Alta calidad    |
| large   | 1550 MB| Muy lento | Máxima    | Máxima calidad  |

## 🔧 Solución de Problemas

### Error de Conexión MySQL
```bash
# Verificar conectividad desde el contenedor
docker-compose run --rm audio-to-text \
  python -c "from database import DatabaseManager; db = DatabaseManager(); print('Conexión:', db.test_connection())"

# Verificar configuración
docker-compose run --rm audio-to-text \
  python -c "from config import Config; c = Config(); print(f'Host: {c.MYSQL_HOST}, DB: {c.MYSQL_DATABASE}')"
```

### Error de Descarga de Audio
```bash
# Verificar acceso a URLs desde el contenedor
docker-compose run --rm audio-to-text \
  python -c "import requests; print('Test URL:', requests.get('https://tvc-voximplant.sfo3.digitaloceanspaces.com/2025/06/27/test.mp3', timeout=5).status_code)"

# Verificar configuración de red
docker-compose run --rm audio-to-text ping google.com
```

### Error de NumPy/Whisper
```bash
# Si ves error "Numpy is not available" o conflictos de NumPy 2.x
# Reconstruir la imagen con versiones compatibles
docker-compose down
docker-compose build --no-cache

# Verificar que NumPy se instaló correctamente
docker-compose run --rm audio-to-text \
  python -c "import numpy; print('NumPy version:', numpy.__version__)"
```

### Error de Memoria
```bash
# Reducir concurrencia en .env
echo "MAX_CONCURRENT_TRANSCRIPTIONS=1" >> .env
echo "WHISPER_MODEL=tiny" >> .env

# Verificar uso de memoria
docker stats audio-to-text-processor
```

### Error de Permisos
```bash
# Verificar permisos de directorios
ls -la audios/ textos/ logs/

# Corregir permisos si es necesario
chmod -R 755 audios/ textos/ logs/
```

### Verificar Procesamiento
```bash
# Ver logs en tiempo real
docker-compose logs -f audio-to-text

# Ver logs específicos
tail -f logs/processing.log

# Verificar archivos generados
find audios/ -name "*.mp3" | head -5
find textos/ -name "*.txt" | head -5

# Verificar tamaño de archivos
du -sh audios/ textos/
```

### Reconstruir Todo
```bash
# Limpiar contenedores e imágenes
docker-compose down
docker system prune -f

# Reconstruir desde cero
docker-compose build --no-cache
```

### Debugging Avanzado
```bash
# Entrar al contenedor para debugging
docker-compose run --rm audio-to-text bash

# Dentro del contenedor:
python -c "import whisper; print('Whisper disponible')"
python -c "import mysql.connector; print('MySQL connector disponible')"
python main.py --start-date 2024-01-01 --end-date 2024-01-31 --dry-run
```

## Personalización

### Consulta SQL Personalizada

Puedes usar tu propia consulta SQL pasándola como parámetro:

```bash
docker-compose run --rm audio-to-text \
  python main.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --query "SELECT id, fecha_llamada, user_type, audio_path FROM llamadas WHERE user_type IN ('cliente', 'agente') AND DATE(fecha_llamada) BETWEEN %s AND %s ORDER BY fecha_llamada"
```

### Modificar Configuración

Edita `config.py` para ajustar:
- Formatos de archivo
- Estructura de carpetas
- Configuración de Whisper
- Límites de procesamiento

## Rendimiento

- **Procesamiento paralelo**: Descarga y transcripción simultáneas
- **Reutilización**: No reprocesa archivos ya transcritos
- **Memoria optimizada**: Configuración de recursos en docker-compose
- **Logs detallados**: Seguimiento completo del proceso

## Soporte

Para problemas o mejoras, revisa los logs en `./logs/` y ajusta la configuración según tus necesidades.
