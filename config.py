import os
import multiprocessing
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de MySQL
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'llamadas')
    
    # Configuración de archivos
    AUDIO_BASE_URL = os.getenv('AUDIO_BASE_URL', '')
    AUDIO_DOWNLOAD_PATH = '/app/audios'
    TEXT_OUTPUT_PATH = '/app/textos'
    
    # Configuración de Whisper
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large')  # tiny, base, small, medium, large
    
    # Configuración de procesamiento
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
    MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv('MAX_CONCURRENT_TRANSCRIPTIONS', 2))
    
    # Configuración optimizada para CPU
    CPU_OPTIMIZED = os.getenv('CPU_OPTIMIZED', 'true').lower() == 'true'
    # Detectar automáticamente el número de CPUs disponibles
    _DETECTED_CPUS = multiprocessing.cpu_count()
    
    # Manejar MAX_CPU_WORKERS con soporte para 'auto'
    _max_cpu_workers_env = os.getenv('MAX_CPU_WORKERS', str(_DETECTED_CPUS))
    if _max_cpu_workers_env.lower() == 'auto':
        MAX_CPU_WORKERS = _DETECTED_CPUS
    else:
        MAX_CPU_WORKERS = int(_max_cpu_workers_env)
    ENABLE_PARALLEL_DOWNLOADS = os.getenv('ENABLE_PARALLEL_DOWNLOADS', 'true').lower() == 'true'
    ENABLE_PARALLEL_TRANSCRIPTIONS = os.getenv('ENABLE_PARALLEL_TRANSCRIPTIONS', 'true').lower() == 'true'
    
    # Configuración de memoria para CPU
    MAX_MEMORY_USAGE = os.getenv('MAX_MEMORY_USAGE', '8G')  # Límite de memoria
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 5))  # Procesar en chunks de N llamadas
    
    # Configuración de limpieza automática (por defecto: limpiar todo)
    AUTO_CLEANUP = os.getenv('AUTO_CLEANUP', 'true').lower() == 'true'  # Limpiar archivos automáticamente
    CLEANUP_AUDIO_FILES = os.getenv('CLEANUP_AUDIO_FILES', 'true').lower() == 'true'  # Limpiar archivos de audio
    CLEANUP_TEMP_FILES = os.getenv('CLEANUP_TEMP_FILES', 'true').lower() == 'true'  # Limpiar archivos temporales
    KEEP_TRANSCRIPTS = os.getenv('KEEP_TRANSCRIPTS', 'true').lower() == 'true'  # Mantener transcripciones
    CLEANUP_DELAY = int(os.getenv('CLEANUP_DELAY', '0'))  # Delay en segundos antes de limpiar
    
    # Configuración de modelo persistente
    PERSISTENT_MODEL = os.getenv('PERSISTENT_MODEL', 'true').lower() == 'true'  # Mantener modelo en memoria
    MODEL_CACHE_ENABLED = os.getenv('MODEL_CACHE_ENABLED', 'true').lower() == 'true'  # Habilitar cache del modelo