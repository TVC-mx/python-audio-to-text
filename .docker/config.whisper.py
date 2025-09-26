import os
from dotenv import load_dotenv

load_dotenv()

class WhisperServiceConfig:
    # Configuración del modelo
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large')
    WHISPER_CACHE_DIR = os.getenv('WHISPER_CACHE_DIR', '/app/models')
    
    # Configuración del servicio
    PORT = int(os.getenv('PORT', 8000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Configuración de transcripción
    DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'es')
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 100 * 1024 * 1024))  # 100MB
    
    # Configuración de timeout
    TRANSCRIPTION_TIMEOUT = int(os.getenv('TRANSCRIPTION_TIMEOUT', 300))  # 5 minutos
    
    # Configuración de logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
