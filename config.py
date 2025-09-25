import os
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
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    
    # Configuración de procesamiento
    MAX_CONCURRENT_DOWNLOADS = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', 3))
    MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv('MAX_CONCURRENT_TRANSCRIPTIONS', 2))
    
    # Configuración optimizada para CPU
    CPU_OPTIMIZED = os.getenv('CPU_OPTIMIZED', 'true').lower() == 'true'
    MAX_CPU_WORKERS = int(os.getenv('MAX_CPU_WORKERS', 4))  # Número de workers para CPU
    ENABLE_PARALLEL_DOWNLOADS = os.getenv('ENABLE_PARALLEL_DOWNLOADS', 'true').lower() == 'true'
    ENABLE_PARALLEL_TRANSCRIPTIONS = os.getenv('ENABLE_PARALLEL_TRANSCRIPTIONS', 'true').lower() == 'true'
    
    # Configuración de memoria para CPU
    MAX_MEMORY_USAGE = os.getenv('MAX_MEMORY_USAGE', '8G')  # Límite de memoria
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 5))  # Procesar en chunks de N llamadas