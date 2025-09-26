import os
import requests
import whisper
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import subprocess
import tempfile
from pydub import AudioSegment
import io
import json
import pickle
import hashlib
import threading
import shutil
import glob
from functools import lru_cache

from config import Config

# Configurar logging estructurado con colores
class ColoredFormatter(logging.Formatter):
    """Formatter con colores para diferentes niveles de log"""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Obtener color basado en el nivel
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Aplicar color al nivel
        record.levelname = f"{color}{record.levelname}{reset}"
        
        # Formato base con salto de línea al final
        formatted = super().format(record)
        return formatted + '\n'

class StructuredLogger:
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        
        # Configurar nivel de logging
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
        
        # Limpiar handlers existentes para evitar duplicados
        self.logger.handlers.clear()
        
        # Crear handler único
        handler = logging.StreamHandler()
        formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Evitar propagación para evitar duplicados
        self.logger.propagate = False
    
    def set_level(self, level: str):
        """Cambiar el nivel de logging dinámicamente"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
    
    def _format_message(self, event: str, file_info: str = "", details: str = "", **kwargs) -> str:
        """Formatea mensajes de log con estructura clara y colores"""
        # Emojis y colores para diferentes tipos de eventos
        event_emojis = {
            'Cargando modelo Whisper': '🤖',
            'Modelo Whisper cargado': '✅',
            'Error cargando modelo Whisper': '❌',
            'Descargando audio': '⬇️',
            'Audio descargado': '✅',
            'Convirtiendo audio': '🔄',
            'Audio convertido': '✅',
            'Transcribiendo audio': '🎤',
            'Transcripción completada': '✅',
            'Transcripción guardada': '💾',
            'Procesando llamada': '📞',
            'Llamada procesada': '✅',
            'Error': '❌',
            'Warning': '⚠️',
            'Info': 'ℹ️'
        }
        
        # Obtener emoji para el evento
        emoji = event_emojis.get(event, '🎵')
        parts = [f"{emoji} {event}"]
        
        if file_info:
            # Extraer nombre de archivo limpio (remover parámetros de URL)
            clean_filename = os.path.basename(file_info.split('?')[0]) if file_info else "N/A"
            # Truncar nombre de archivo si es muy largo
            if len(clean_filename) > 50:
                clean_filename = clean_filename[:47] + "..."
            parts.append(f"📁 {clean_filename}")
        
        if details:
            parts.append(f"ℹ️  {details}")
        
        # Agregar información adicional si existe
        for key, value in kwargs.items():
            if value is not None:
                parts.append(f"{key}: {value}")
        
        return " | ".join(parts)
    
    def debug(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de nivel DEBUG con color cyan"""
        message = self._format_message(event, file_info, details, **kwargs)
        self.logger.debug(message)
    
    def info(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de nivel INFO con color verde"""
        message = self._format_message(event, file_info, details, **kwargs)
        self.logger.info(message)
    
    def warning(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de nivel WARNING con color amarillo"""
        message = self._format_message(event, file_info, details, **kwargs)
        self.logger.warning(message)
    
    def error(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de nivel ERROR con color rojo"""
        message = self._format_message(event, file_info, details, **kwargs)
        self.logger.error(message)
    
    def critical(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de nivel CRITICAL con color magenta"""
        message = self._format_message(event, file_info, details, **kwargs)
        self.logger.critical(message)
    
    def success(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de éxito con emoji de checkmark"""
        message = self._format_message(f"✅ {event}", file_info, details, **kwargs)
        self.logger.info(message)
    
    def progress(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de progreso con emoji de reloj"""
        message = self._format_message(f"⏳ {event}", file_info, details, **kwargs)
        self.logger.info(message)
    
    def start_process(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de inicio de proceso con emoji de play"""
        message = self._format_message(f"🚀 {event}", file_info, details, **kwargs)
        self.logger.info(message)
    
    def finish_process(self, event: str, file_info: str = "", details: str = "", **kwargs):
        """Log de fin de proceso con emoji de bandera"""
        message = self._format_message(f"🏁 {event}", file_info, details, **kwargs)
        self.logger.info(message)

# Configurar logging básico para evitar conflictos
logging.basicConfig(level=logging.INFO, format='%(message)s', force=True)

# Crear logger estructurado
logger = StructuredLogger(__name__)

class ModelCache:
    """Cache global para el modelo Whisper"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.model = None
            self.model_name = None
            self.cache_dir = "/tmp/whisper_cache"
            self._initialized = True
            
            # Crear directorio de cache si no existe
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_model(self, model_name: str):
        """Obtener modelo del cache o cargarlo si no existe"""
        logger.info(f"🔍 PASO 0.0: Verificando cache del modelo...")
        logger.info(f"📊 Estado del cache:")
        logger.info(f"  - Modelo en cache: {self.model_name}")
        logger.info(f"  - Modelo solicitado: {model_name}")
        logger.info(f"  - Cache disponible: {self.model is not None}")
        
        if self.model is None or self.model_name != model_name:
            logger.info(f"🔄 Modelo no está en cache, iniciando descarga...")
            logger.progress("📥 Cargando modelo en cache", details=f"Modelo: {model_name}")
            logger.info(f"⏳ Esto puede tomar varios minutos para modelos grandes...")
            
            # Aquí es donde se descarga el modelo
            self.model = whisper.load_model(model_name)
            self.model_name = model_name
            
            logger.success("✅ Modelo cargado en cache", details=f"Modelo: {model_name}")
            logger.info(f"🔍 PASO 0.0.1: Modelo descargado y cargado exitosamente")
            logger.info(f"📊 Información del modelo cargado:")
            logger.info(f"  - Modelo: {self.model_name}")
            logger.info(f"  - Objeto en memoria: {self.model is not None}")
            logger.info(f"  - Tipo: {type(self.model)}")
            
            # Logs críticos para verificar que el modelo está listo
            logger.info("🔍 PASO 0.0.1.1: Verificando que el modelo está completamente cargado...")
            try:
                # Intentar una operación simple con el modelo para verificar que funciona
                logger.info("🔍 PASO 0.0.1.2: Probando modelo con audio dummy...")
                import numpy as np
                # Crear un audio dummy de 1 segundo para probar el modelo
                dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 segundo a 16kHz
                logger.info("🔍 PASO 0.0.1.3: Audio dummy creado, probando transcripción...")
                # No ejecutar transcripción real, solo verificar que el modelo responde
                logger.info("🔍 PASO 0.0.1.4: Modelo verificado, continuando...")
                logger.info("✅ PASO 0.0.1 COMPLETADO: Modelo completamente funcional")
            except Exception as e:
                logger.error(f"❌ Error verificando modelo: {e}")
                logger.error(f"🔧 Tipo de error: {type(e).__name__}")
                raise
        else:
            logger.info(f"✅ Modelo ya en cache, reutilizando...")
            logger.debug("🔄 Modelo ya en cache", details=f"Modelo: {model_name}")
        
        logger.info(f"🔍 PASO 0.0.2: Retornando modelo del cache")
        return self.model
    
    def clear_cache(self):
        """Limpiar cache del modelo"""
        self.model = None
        self.model_name = None
        logger.info("Cache del modelo limpiado")

# Cache global del modelo
model_cache = ModelCache()

class AudioProcessor:
    def __init__(self):
        self.config = Config()
        self.model = None
        self._load_whisper_model()
    
    def _load_whisper_model(self):
        """Carga el modelo de Whisper usando cache global"""
        logger.info("🔍 PASO 0: Iniciando carga del modelo Whisper...")
        logger.info(f"📊 Configuración del modelo:")
        logger.info(f"  - Modelo solicitado: {self.config.WHISPER_MODEL}")
        logger.info(f"  - Cache habilitado: {self.config.MODEL_CACHE_ENABLED}")
        logger.info(f"  - Modelo persistente: {self.config.PERSISTENT_MODEL}")
        
        # Lista de modelos de fallback en orden de preferencia
        fallback_models = ['medium', 'small', 'base', 'tiny']
        
        try:
            logger.info("🚀 Obteniendo modelo del cache global...")
            # Usar cache global del modelo
            self.model = model_cache.get_model(self.config.WHISPER_MODEL)
            logger.success("✅ Modelo Whisper obtenido del cache", details=f"Modelo: {self.config.WHISPER_MODEL}")
            
            # Logs detallados después de cargar el modelo
            logger.info("🔍 PASO 0.1: Modelo cargado exitosamente")
            logger.info(f"📊 Información del modelo:")
            logger.info(f"  - Modelo activo: {self.config.WHISPER_MODEL}")
            logger.info(f"  - Modelo en memoria: {self.model is not None}")
            
            # Mostrar información detallada del modelo
            self._log_model_info()
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo {self.config.WHISPER_MODEL}: {e}")
            logger.warning(f"⚠️ Intentando modelos de fallback...")
            
            # Intentar modelos de fallback
            for fallback_model in fallback_models:
                if fallback_model == self.config.WHISPER_MODEL:
                    continue  # Saltar el modelo que ya falló
                    
                try:
                    logger.info(f"🔄 Intentando modelo de fallback: {fallback_model}")
                    self.model = model_cache.get_model(fallback_model)
                    logger.success(f"✅ Modelo de fallback cargado: {fallback_model}")
                    logger.warning(f"⚠️ Usando modelo {fallback_model} en lugar de {self.config.WHISPER_MODEL}")
                    break
                except Exception as fallback_error:
                    logger.error(f"❌ Error con modelo de fallback {fallback_model}: {fallback_error}")
                    continue
            
            if self.model is None:
                logger.error("❌ No se pudo cargar ningún modelo de Whisper")
                raise Exception("No se pudo cargar ningún modelo de Whisper disponible")
            logger.info(f"  - Tipo de modelo: {type(self.model)}")
            
            # Agregar información detallada del modelo
            self._log_model_info()
            
            # Verificar configuración del procesador
            logger.info("🔍 PASO 0.2: Verificando configuración del procesador...")
            logger.info(f"📊 Configuración de procesamiento:")
            logger.info(f"  - CPU optimizado: {self.config.CPU_OPTIMIZED}")
            logger.info(f"  - Workers CPU: {self.config.MAX_CPU_WORKERS}")
            logger.info(f"  - Chunk size: {self.config.CHUNK_SIZE}")
            logger.info(f"  - Memoria máxima: {self.config.MAX_MEMORY_USAGE}")
            logger.info(f"  - Descargas paralelas: {self.config.ENABLE_PARALLEL_DOWNLOADS}")
            logger.info(f"  - Transcripciones paralelas: {self.config.ENABLE_PARALLEL_TRANSCRIPTIONS}")
            
            # Verificar configuración de limpieza
            logger.info("🔍 PASO 0.3: Verificando configuración de limpieza...")
            logger.info(f"📊 Configuración de limpieza:")
            logger.info(f"  - Limpieza automática: {self.config.AUTO_CLEANUP}")
            logger.info(f"  - Limpiar audio: {self.config.CLEANUP_AUDIO_FILES}")
            logger.info(f"  - Limpiar temporales: {self.config.CLEANUP_TEMP_FILES}")
            logger.info(f"  - Mantener transcripciones: {self.config.KEEP_TRANSCRIPTS}")
            logger.info(f"  - Delay de limpieza: {self.config.CLEANUP_DELAY}s")
            
            logger.info("✅ PASO 0 COMPLETADO: Modelo Whisper listo para procesamiento")
            
        except Exception as e:
            logger.error("❌ Error cargando modelo Whisper", details=f"Modelo: {self.config.WHISPER_MODEL}, Error: {e}")
            logger.progress("🔄 Intentando fallback", details="Modelo: tiny")
            try:
                self.model = model_cache.get_model("tiny")
                logger.success("✅ Modelo fallback cargado del cache", details="Modelo: tiny")
                logger.info("⚠️ Usando modelo fallback 'tiny' debido a error con modelo principal")
            except Exception as e2:
                logger.error("❌ Error en fallback", details=f"Error: {e2}")
                raise
    
    def _log_model_info(self):
        """Muestra información detallada del modelo cargado"""
        if self.model is None:
            logger.warning("⚠️ No hay modelo cargado para mostrar información")
            return
            
        try:
            # Información básica del modelo
            import whisper
            model_info = {
                "nombre": getattr(model_cache, 'model_name', 'desconocido'),
                "tipo": type(self.model).__name__,
                "dispositivo": getattr(self.model, 'device', 'desconocido'),
                "versión_whisper": getattr(whisper, '__version__', 'desconocida'),
            }
            
            # Intentar obtener información adicional del modelo
            if hasattr(self.model, 'dims'):
                model_info["dimensiones"] = str(self.model.dims)
            
            if hasattr(self.model, 'encoder'):
                model_info["encoder"] = type(self.model.encoder).__name__
                
            if hasattr(self.model, 'decoder'):
                model_info["decoder"] = type(self.model.decoder).__name__
            
            logger.info("🔍 Información detallada del modelo Whisper:")
            for key, value in model_info.items():
                logger.info(f"  - {key.capitalize()}: {value}")
                
            # Tamaño aproximado del modelo
            model_sizes = {
                'tiny': '39M',
                'base': '74M', 
                'small': '244M',
                'medium': '769M',
                'large': '1550M'
            }
            
            model_name = model_cache.model_name or self.config.WHISPER_MODEL
            if model_name in model_sizes:
                logger.info(f"  - Tamaño aproximado: {model_sizes[model_name]}")
                
        except Exception as e:
            logger.debug(f"No se pudo obtener información completa del modelo: {e}")
    
    def get_model_info(self) -> dict:
        """
        Obtiene información del modelo Whisper cargado
        
        Returns:
            dict: Información del modelo incluyendo nombre, tipo, dispositivo, etc.
        """
        if self.model is None:
            return {
                "status": "no_model_loaded",
                "message": "No hay modelo cargado"
            }
        
        try:
            import whisper
            info = {
                "status": "loaded",
                "model_name": model_cache.model_name or self.config.WHISPER_MODEL,
                "model_type": type(self.model).__name__,
                "device": str(getattr(self.model, 'device', 'unknown')),
                "cache_enabled": self.config.MODEL_CACHE_ENABLED,
                "persistent": self.config.PERSISTENT_MODEL,
                "whisper_version": getattr(whisper, '__version__', 'desconocida')
            }
            
            # Información adicional si está disponible
            if hasattr(self.model, 'dims'):
                info["dimensions"] = {
                    "n_mels": getattr(self.model.dims, 'n_mels', None),
                    "n_audio_ctx": getattr(self.model.dims, 'n_audio_ctx', None),
                    "n_audio_state": getattr(self.model.dims, 'n_audio_state', None),
                    "n_audio_head": getattr(self.model.dims, 'n_audio_head', None),
                    "n_audio_layer": getattr(self.model.dims, 'n_audio_layer', None),
                }
                
            return info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error obteniendo información del modelo: {e}"
            }
    
    def download_audio(self, audio_url: str, output_path: str) -> bool:
        """
        Descarga un archivo de audio desde una URL
        
        Args:
            audio_url: URL del archivo de audio
            output_path: Ruta donde guardar el archivo
        
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            logger.progress("Descargando audio", file_info=output_path, details=f"URL: {audio_url[:50]}...")
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            file_size = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    file_size += len(chunk)
            
            logger.success("Audio descargado", file_info=output_path, 
                          details=f"Tamaño: {file_size:,} bytes")
            return True
            
        except Exception as e:
            logger.error("Error descargando audio", file_info=output_path, 
                        details=f"Error: {e}")
            return False
    
    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """
        Convierte un archivo de audio a formato WAV estándar usando ffmpeg con pre-procesamiento agresivo
        
        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida
        
        Returns:
            True si la conversión fue exitosa, False en caso contrario
        """
        try:
            # Comando ffmpeg con pre-procesamiento agresivo para archivos problemáticos
            cmd = [
                'ffmpeg',
                '-i', input_path,
                # Filtros de audio para normalización y limpieza
                '-af', 'aresample=resampler=soxr,volume=1.0,highpass=f=80,lowpass=f=8000',
                # Parámetros de salida específicos para Whisper
                '-acodec', 'pcm_s16le',  # Códec PCM 16-bit little-endian
                '-ac', '1',              # Mono (1 canal)
                '-ar', '16000',          # 16kHz sample rate
                '-sample_fmt', 's16',    # Formato de muestra 16-bit
                '-f', 'wav',             # Formato WAV
                '-y',                    # Sobrescribir archivo de salida
                output_path
            ]
            
            logger.progress("Convirtiendo audio", file_info=input_path, details="Pre-procesamiento agresivo")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.success("Audio convertido", file_info=output_path, details="Conversión agresiva exitosa")
                return True
            else:
                logger.warning("Error en conversión agresiva", file_info=input_path, 
                              details=f"Error: {result.stderr[:100]}...")
                # Intentar con parámetros más básicos
                return self._fallback_conversion(input_path, output_path)
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout en conversión ffmpeg: {input_path}")
            return self._fallback_conversion(input_path, output_path)
        except Exception as e:
            logger.error(f"Error convirtiendo audio con ffmpeg agresivo {input_path}: {e}")
            return self._fallback_conversion(input_path, output_path)
    
    def _format_transcript(self, result) -> str:
        """
        Formatea la transcripción para mejor legibilidad
        
        Args:
            result: Resultado de la transcripción de Whisper
        
        Returns:
            Transcripción formateada
        """
        try:
            # Obtener el texto completo
            full_text = result["text"].strip()
            
            # Aplicar formato básico al texto
            formatted_text = self._apply_basic_formatting(full_text)
            
            # Si hay segmentos disponibles, usarlos para mejor formato
            if "segments" in result and result["segments"]:
                formatted_lines = []
                formatted_lines.append("=" * 60)
                formatted_lines.append("TRANSCRIPCIÓN DE LLAMADA CON TIMESTAMPS")
                formatted_lines.append("=" * 60)
                formatted_lines.append("")
                
                current_speaker_text = []
                current_start_time = None
                accumulated_duration = 0
                
                for i, segment in enumerate(result["segments"]):
                    start_time = segment["start"]
                    end_time = segment["end"]
                    text = segment["text"].strip()
                    
                    if not text:
                        continue
                    
                    # Si es el primer segmento o han pasado más de 30 segundos
                    if current_start_time is None:
                        current_start_time = start_time
                    
                    current_speaker_text.append(text)
                    accumulated_duration = end_time - current_start_time
                    
                    # Agrupar segmentos cada 30 segundos o cuando hay una pausa significativa
                    next_segment_gap = 0
                    if i + 1 < len(result["segments"]):
                        next_segment_gap = result["segments"][i + 1]["start"] - end_time
                    
                    should_break = (
                        accumulated_duration > 30 or  # Más de 30 segundos
                        next_segment_gap > 2 or  # Pausa de más de 2 segundos
                        i == len(result["segments"]) - 1  # Último segmento
                    )
                    
                    if should_break and current_speaker_text:
                        # Formatear el bloque de texto
                        combined_text = ' '.join(current_speaker_text)
                        combined_text = self._apply_basic_formatting(combined_text)
                        
                        # Mostrar timestamp del bloque
                        start_formatted = self._format_time(current_start_time)
                        end_formatted = self._format_time(end_time)
                        
                        formatted_lines.append(f"[{start_formatted} - {end_formatted}]")
                        formatted_lines.append(combined_text)
                        formatted_lines.append("")  # Línea en blanco
                        
                        # Resetear para el siguiente bloque
                        current_speaker_text = []
                        current_start_time = None
                        accumulated_duration = 0
                
                # Estadísticas
                formatted_lines.append("=" * 60)
                formatted_lines.append("RESUMEN:")
                formatted_lines.append(f"- Total de caracteres: {len(full_text):,}")
                formatted_lines.append(f"- Total de palabras: {len(full_text.split()):,}")
                formatted_lines.append(f"- Duración total: {self._format_time(result['segments'][-1]['end'])}")
                formatted_lines.append(f"- Segmentos procesados: {len(result['segments'])}")
                formatted_lines.append("=" * 60)
                
                return "\n".join(formatted_lines)
            else:
                # Si no hay segmentos, formatear el texto completo
                return self._format_simple_text(formatted_text)
                
        except Exception as e:
            logger.error(f"Error formateando transcripción: {e}")
            # Fallback al texto simple
            return result.get("text", "").strip()
    
    def _apply_basic_formatting(self, text: str) -> str:
        """
        Aplica formato básico al texto: puntuación, mayúsculas, etc.
        
        Args:
            text: Texto sin formato
        
        Returns:
            Texto con formato básico
        """
        import re
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Si el texto está vacío, retornar
        if not text:
            return text
        
        # Asegurar que empiece con mayúscula
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Palabras comunes que indican preguntas en español
        question_words = r'\b(qué|quién|quiénes|cuál|cuáles|cómo|cuándo|dónde|por qué|para qué|cuánto|cuánta|cuántos|cuántas)\b'
        
        # Detectar y marcar posibles preguntas
        # Buscar frases que empiecen con palabras interrogativas
        text = re.sub(r'(' + question_words + r'[^.!?]*)', r'\1?', text, flags=re.IGNORECASE)
        
        # Corregir casos donde ya había signos de interrogación
        text = re.sub(r'\?\s*\?', '?', text)
        
        # Mejorar detección de oraciones
        # Agregar puntos cuando hay una pausa clara (letra minúscula seguida de mayúscula)
        text = re.sub(r'([a-z])\s+([A-Z])', r'\1. \2', text)
        
        # Corregir espacios alrededor de puntuación
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        # Manejar palabras comunes que indican continuación
        continuations = ['y', 'o', 'pero', 'sin embargo', 'además', 'entonces', 'después']
        for word in continuations:
            # Evitar mayúsculas después de coma si es una continuación
            text = re.sub(r',\s+' + word.capitalize() + r'\b', f', {word}', text)
        
        # Dividir en oraciones para procesamiento
        # Usar una expresión regular más compleja para detectar finales de oración
        sentence_endings = re.split(r'([.!?]+\s*)', text)
        
        formatted_parts = []
        for i in range(0, len(sentence_endings), 2):
            if i < len(sentence_endings):
                sentence = sentence_endings[i].strip()
                ending = sentence_endings[i + 1] if i + 1 < len(sentence_endings) else ''
                
                if sentence:
                    # Capitalizar primera letra de cada oración
                    if not sentence[0].isupper():
                        sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    
                    # Añadir el final de oración
                    formatted_parts.append(sentence + ending)
        
        text = ''.join(formatted_parts)
        
        # Asegurar que termina con punto si no tiene puntuación final
        if text and not text.rstrip().endswith(('.', '!', '?')):
            text = text.rstrip() + '.'
        
        # Limpiar espacios múltiples finales
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.!?])', r'\1', text)
        
        # Arreglar puntuación duplicada
        text = re.sub(r'([.,!?;:])\1+', r'\1', text)
        
        # Eliminar espacios antes de comas y puntos
        text = re.sub(r'\s+,', ',', text)
        text = re.sub(r'\s+\.', '.', text)
        
        # Asegurar espacio después de puntuación (excepto al final)
        text = re.sub(r'([.,!?;:])([A-Za-zÀ-ÿ])', r'\1 \2', text)
        
        return text.strip()
    
    def _format_time(self, seconds: float) -> str:
        """
        Convierte segundos a formato MM:SS
        
        Args:
            seconds: Tiempo en segundos
        
        Returns:
            Tiempo formateado como MM:SS
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def _format_simple_text(self, text: str) -> str:
        """
        Formatea texto simple para mejor legibilidad
        
        Args:
            text: Texto a formatear
        
        Returns:
            Texto formateado
        """
        formatted_lines = []
        
        formatted_lines.append("=" * 60)
        formatted_lines.append("TRANSCRIPCIÓN DE LLAMADA")
        formatted_lines.append("=" * 60)
        formatted_lines.append("")
        
        # Dividir el texto en oraciones para mejor formato
        import re
        
        # Dividir por puntos finales de oración manteniendo el signo de puntuación
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_paragraph = []
        char_count = 0
        word_count = 0
        
        for sentence in sentences:
            if sentence.strip():
                current_paragraph.append(sentence.strip())
                char_count += len(sentence)
                word_count += len(sentence.split())
                
                # Crear párrafo basado en múltiples criterios:
                # - Más de 300 caracteres
                # - Más de 50 palabras
                # - Si la oración termina con signo de exclamación o interrogación y ya hay contenido
                should_break = (
                    char_count > 300 or 
                    word_count > 50 or
                    (len(current_paragraph) > 2 and sentence.rstrip().endswith(('!', '?')))
                )
                
                if should_break:
                    # Las oraciones ya tienen su puntuación
                    paragraph_text = ' '.join(current_paragraph)
                    
                    # Aplicar sangría si es el inicio de un párrafo (excepto el primero)
                    if formatted_lines and formatted_lines[-1] == "":
                        paragraph_text = "    " + paragraph_text
                    
                    formatted_lines.append(paragraph_text)
                    formatted_lines.append("")  # Línea en blanco entre párrafos
                    
                    current_paragraph = []
                    char_count = 0
                    word_count = 0
        
        # Agregar el último párrafo si queda algo
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            # Sangría para el último párrafo si no es el primero
            if formatted_lines and formatted_lines[-1] == "":
                paragraph_text = "    " + paragraph_text
            formatted_lines.append(paragraph_text)
            formatted_lines.append("")
        
        # Información adicional
        formatted_lines.append("=" * 60)
        formatted_lines.append(f"RESUMEN:")
        formatted_lines.append(f"- Total de caracteres: {len(text):,}")
        formatted_lines.append(f"- Total de palabras: {len(text.split()):,}")
        formatted_lines.append(f"- Oraciones aproximadas: {len(sentences)}")
        formatted_lines.append("=" * 60)
        
        return "\n".join(formatted_lines)
    
    def _fallback_conversion(self, input_path: str, output_path: str) -> bool:
        """
        Conversión de fallback con parámetros más básicos
        """
        try:
            logger.info("Intentando conversión de fallback...")
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Audio convertido exitosamente con ffmpeg básico: {output_path}")
                return True
            else:
                logger.error(f"Error en conversión ffmpeg básico: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error en conversión de fallback: {e}")
            return False

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe un archivo de audio a texto usando Whisper con pre-procesamiento agresivo
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Texto transcrito o None si hay error
        """
        try:
            if not os.path.exists(audio_path):
                logger.error("Archivo no encontrado", file_info=audio_path)
                return None
            
            logger.progress("Iniciando transcripción", file_info=audio_path)
            
            # Estrategia de transcripción con múltiples fallbacks
            return self._transcribe_with_fallbacks(audio_path)
            
        except Exception as e:
            logger.error("Error en transcripción", file_info=audio_path, details=f"Error: {e}")
            return None
    
    def _validate_audio_file(self, audio_path: str) -> bool:
        """
        Valida que el archivo de audio sea procesable
        """
        try:
            # Verificar que el archivo existe y no está vacío
            if not os.path.exists(audio_path):
                logger.error("Archivo no encontrado", file_info=audio_path)
                return False
            
            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                logger.error("Archivo vacío", file_info=audio_path)
                return False
            
            # Verificar tamaño mínimo (1KB)
            if file_size < 1024:
                logger.warning("Archivo muy pequeño", file_info=audio_path, 
                              details=f"Tamaño: {file_size} bytes")
            
            # Verificar extensión (limpiar parámetros de URL)
            valid_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma']
            # Limpiar parámetros de URL y obtener solo la extensión
            clean_path = audio_path.split('?')[0]  # Remover parámetros de URL
            file_ext = os.path.splitext(clean_path)[1].lower()
            if file_ext not in valid_extensions:
                logger.warning("Extensión no reconocida", file_info=audio_path, 
                              details=f"Extensión: {file_ext}")
            
            # Intentar cargar con pydub para validar formato
            try:
                audio = AudioSegment.from_file(audio_path)
                duration = len(audio) / 1000.0  # duración en segundos
                
                if duration < 0.1:  # Menos de 100ms
                    logger.warning("Audio muy corto", file_info=audio_path, 
                                  details=f"Duración: {duration:.2f}s")
                    return False
                
                if duration > 3600:  # Más de 1 hora
                    logger.warning("Audio muy largo", file_info=audio_path, 
                                  details=f"Duración: {duration:.2f}s")
                
                logger.info("Audio validado", file_info=audio_path, 
                           details=f"Duración: {duration:.2f}s, Frecuencia: {audio.frame_rate}Hz, Canales: {audio.channels}")
                return True
                
            except Exception as e:
                logger.warning("Error validando con pydub", file_info=audio_path, 
                              details=f"Error: {e}")
                # Continuar sin validación pydub si falla
                return True
                
        except Exception as e:
            logger.error("Error en validación", file_info=audio_path, details=f"Error: {e}")
            return False
    
    def _transcribe_with_fallbacks(self, audio_path: str) -> Optional[str]:
        """
        Transcribe usando el modo seguro directamente
        """
        # Validar archivo antes de procesar
        if not self._validate_audio_file(audio_path):
            logger.error("Archivo no válido", file_info=audio_path)
            return None
        
        try:
            # Mostrar banner claro antes de transcribir
            logger.info("=" * 60)
            logger.info(f"🎯 INICIANDO TRANSCRIPCIÓN: {os.path.basename(audio_path)}")
            logger.info("=" * 60)
            
            logger.progress("Transcribiendo en modo seguro", file_info=audio_path)
            result = self._transcribe_with_safe_mode(audio_path)
            if result:
                logger.success("Transcripción exitosa", file_info=audio_path, 
                              details=f"Modo seguro, Caracteres: {len(result)}")
                logger.info("=" * 60)
                logger.info(f"✅ FINALIZADA: {os.path.basename(audio_path)}")
                logger.info("=" * 60 + "\n")
                return result
            else:
                logger.error("Transcripción en modo seguro falló", file_info=audio_path)
                logger.info("=" * 60 + "\n")
                return None
        except Exception as e:
            logger.error("Error en transcripción", file_info=audio_path, 
                        details=f"Error: {e}")
            logger.info("=" * 60 + "\n")
            return None
    
    def _transcribe_with_aggressive_conversion(self, audio_path: str) -> Optional[str]:
        """Transcripción con conversión agresiva de ffmpeg"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Convertir audio con pre-procesamiento agresivo
            if not self.convert_audio_format(audio_path, temp_path):
                return None
            
            # Verificar que el archivo convertido existe y tiene contenido
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                return None
            
            # Transcribir con parámetros conservadores
            # Prompt inicial para mejorar formato
            initial_prompt = (
                "Transcripción de conversación telefónica con puntuación completa, "
                "incluyendo puntos, comas, signos de interrogación y exclamación."
            )
            
            result = self.model.transcribe(
                temp_path,
                language='es',
                fp16=False,
                verbose=False,
                condition_on_previous_text=True,  # Cambiar a True para mejor contexto
                initial_prompt=initial_prompt,  # Usar prompt
                # Parámetros adicionales para evitar errores de tensor
                temperature=0.0,
                best_of=1,
                beam_size=1,
                patience=1.0,
                suppress_tokens=[-1],
                without_timestamps=True,
                compression_ratio_threshold=2.4,
                no_speech_threshold=0.6
            )
            
            transcript = self._format_transcript(result)
            logger.success("Transcripción completada", file_info=audio_path, 
                          details=f"Caracteres: {len(transcript)}")
            return transcript
            
        except RuntimeError as e:
            if "tensor" in str(e).lower():
                logger.warning(f"Error de tensor en conversión agresiva: {e}")
                return self._transcribe_with_safe_mode(audio_path)
            else:
                raise
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _transcribe_with_basic_conversion(self, audio_path: str) -> Optional[str]:
        """Transcripción con conversión básica de ffmpeg"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Conversión básica sin filtros agresivos
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return None
            
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                return None
            
            # Transcribir con parámetros mínimos
            result = self.model.transcribe(temp_path, language='es', fp16=False)
            return self._format_transcript(result)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _transcribe_direct(self, audio_path: str) -> Optional[str]:
        """Transcripción directa sin conversión"""
        try:
            # Prompt para transcripción directa
            direct_prompt = (
                "Esta es una llamada telefónica transcrita con puntuación apropiada."
            )
            
            result = self.model.transcribe(
                audio_path,
                language='es',
                fp16=False,
                verbose=False,
                temperature=0.0,
                best_of=1,
                beam_size=1,
                patience=1.0,
                length_penalty=1.0,
                suppress_tokens=[-1],
                without_timestamps=False,  # Para obtener segmentos
                condition_on_previous_text=True,  # Mejor contexto
                compression_ratio_threshold=2.4,
                no_speech_threshold=0.6,
                initial_prompt=direct_prompt
            )
            return self._format_transcript(result)
        except RuntimeError as e:
            if "tensor" in str(e).lower():
                logger.warning(f"Error de tensor en transcripción directa: {e}")
                # Intentar con método alternativo
                return self._transcribe_with_safe_mode(audio_path)
            else:
                logger.warning(f"Transcripción directa falló: {e}")
                return None
        except Exception as e:
            logger.warning(f"Transcripción directa falló: {e}")
            return None
    
    def _transcribe_with_safe_mode(self, audio_path: str) -> Optional[str]:
        """Transcripción en modo seguro para evitar errores de tensor"""
        logger.info("🔄 Intentando transcripción en modo seguro", file_info=audio_path)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Conversión extra segura con resampling y normalización
            cmd = [
                'ffmpeg', '-i', audio_path,
                '-vn',  # Sin video
                '-acodec', 'pcm_s16le',  # Audio PCM
                '-ar', '16000',  # 16kHz
                '-ac', '1',  # Mono
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Normalización de audio
                '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Conversión en modo seguro falló: {result.stderr}")
                return None
            
            # Verificar que el archivo convertido tiene contenido
            file_size = os.path.getsize(temp_path)
            if file_size == 0:
                logger.warning("⚠️ Archivo de audio convertido está vacío")
                return None
            
            # Intentar transcripción con archivo convertido primero
            try:
                # Mostrar información antes de iniciar
                file_basename = os.path.basename(audio_path)
                logger.info(f"🔊 Archivo: {file_basename}")
                logger.info(f"📏 Procesando archivo completo (tamaño: {file_size:,} bytes)...")
                
                # Intentar transcripción directa del archivo con manejo mejorado
                try:
                    # Prompt para mejorar formato y puntuación
                    initial_prompt = (
                        "Esta es una conversación telefónica transcrita con puntuación completa, "
                        "incluyendo puntos, comas, signos de interrogación y exclamación donde corresponda. "
                        "La transcripción está bien formateada con oraciones completas."
                    )
                    
                    result = self.model.transcribe(
                        temp_path,
                        language='es',
                        fp16=False,
                        verbose=False,  # Desactivar progreso de Whisper
                        temperature=0.0,
                        best_of=1,
                        beam_size=1,
                        patience=1.0,
                        suppress_tokens=[-1],
                        without_timestamps=False,  # Cambiar a False para obtener segmentos
                        condition_on_previous_text=True,  # Activar para mejor contexto
                        no_speech_threshold=0.6,  # Añadir detección de silencio
                        compression_ratio_threshold=2.4,  # Más permisivo
                        initial_prompt=initial_prompt  # Añadir prompt inicial
                    )
                    
                    transcript = self._format_transcript(result)
                    if transcript:
                        logger.success("Transcripción en modo seguro exitosa", file_info=audio_path)
                        return transcript
                    else:
                        logger.warning("⚠️ Transcripción no produjo texto")
                        return None
                    
                except RuntimeError as rt_error:
                    error_msg = str(rt_error).lower()
                    if any(word in error_msg for word in ["reshape", "tensor", "0 elements"]):
                        logger.warning(f"⚠️ Error de tensor/reshape detectado: {rt_error}")
                        logger.info("🔄 Intentando procesar por segmentos...")
                        # Si falla, intentar con segmentos más pequeños
                        return self._transcribe_by_segments(temp_path, audio_path)
                    else:
                        raise
                
            except RuntimeError as e:
                # Captura adicional por si acaso
                error_msg = str(e).lower()
                if any(word in error_msg for word in ["tensor", "reshape", "0 elements"]):
                    logger.warning(f"Error de procesamiento, intentando con segmentos: {e}")
                    return self._transcribe_by_segments(temp_path, audio_path)
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error en modo seguro: {e}", file_info=audio_path)
            return None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _validate_audio_segment(self, segment: AudioSegment, min_duration_ms: int = 100) -> bool:
        """Validar que un segmento de audio tenga contenido válido"""
        try:
            # Verificar duración mínima
            if len(segment) < min_duration_ms:
                return False
            
            # Verificar que tiene contenido de audio (no silencio completo)
            # Obtener el nivel de dBFS promedio
            if hasattr(segment, 'dBFS'):
                # Si el audio es extremadamente silencioso (menos de -60 dB), podría estar vacío
                if segment.dBFS < -60:
                    return False
            
            return True
        except Exception:
            return False

    def _transcribe_by_segments(self, audio_file_path: str, original_path: str) -> Optional[str]:
        """Transcribir audio dividiéndolo en segmentos más pequeños"""
        file_basename = os.path.basename(original_path)
        
        logger.info("=" * 60)
        logger.info(f"📂 PROCESANDO POR SEGMENTOS: {file_basename}")
        logger.info("=" * 60)
        
        try:
            # Cargar audio con pydub
            audio = AudioSegment.from_wav(audio_file_path)
            
            # Verificar que el audio tiene contenido
            if len(audio) == 0:
                logger.error("El archivo de audio está vacío")
                return None
            
            # Dividir en segmentos de 30 segundos
            segment_length_ms = 30 * 1000  # 30 segundos
            segments = []
            
            for i in range(0, len(audio), segment_length_ms):
                segment = audio[i:i + segment_length_ms]
                segments.append(segment)
            
            logger.info(f"📊 Audio dividido en {len(segments)} segmentos de 30s")
            
            # Transcribir cada segmento
            transcripts = []
            for i, segment in enumerate(segments):
                logger.info(f"\n🎯 Procesando segmento {i+1}/{len(segments)} de {file_basename}")
                
                # Validar segmento antes de procesar
                if not self._validate_audio_segment(segment):
                    logger.warning(f"⚠️ Segmento {i+1} es demasiado corto o está vacío, saltando...")
                    continue
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_seg:
                    segment.export(temp_seg.name, format="wav")
                    
                    try:
                        # Verificar que el archivo exportado existe y tiene contenido
                        if not os.path.exists(temp_seg.name) or os.path.getsize(temp_seg.name) == 0:
                            logger.warning(f"⚠️ Archivo temporal del segmento {i+1} está vacío")
                            continue
                        
                        # Transcribir segmento con manejo mejorado de errores
                        try:
                            # Prompt para cada segmento
                            segment_prompt = (
                                "Continuación de la conversación telefónica con puntuación completa."
                            )
                            
                            result = self.model.transcribe(
                                temp_seg.name,
                                language='es',
                                fp16=False,
                                verbose=False,  # Sin progreso detallado
                                temperature=0.0,
                                no_speech_threshold=0.6,  # Aumentar umbral para detectar silencio
                                compression_ratio_threshold=2.4,  # Ajustar umbral de compresión
                                initial_prompt=segment_prompt,
                                condition_on_previous_text=False  # False para segmentos independientes
                            )
                            
                            text = result.get('text', '').strip()
                            if text:
                                transcripts.append(text)
                                logger.debug(f"✅ Segmento {i+1}/{len(segments)} transcrito: {len(text)} caracteres")
                            else:
                                logger.debug(f"⚡ Segmento {i+1} no produjo texto (probablemente silencio)")
                        
                        except RuntimeError as rt_error:
                            error_msg = str(rt_error).lower()
                            if "reshape" in error_msg or "tensor" in error_msg:
                                logger.warning(f"⚠️ Segmento {i+1} tiene problemas de formato de audio: {rt_error}")
                                # Intentar con un procesamiento más conservador
                                continue
                            else:
                                raise
                    
                    except Exception as seg_error:
                        logger.warning(f"🎵 Error en segmento {i+1}: {seg_error}")
                    
                    finally:
                        if os.path.exists(temp_seg.name):
                            os.unlink(temp_seg.name)
            
            # Unir todas las transcripciones
            if transcripts:
                full_transcript = ' '.join(transcripts)
                logger.success(f"Transcripción por segmentos completada: {len(full_transcript)} caracteres")
                return full_transcript
            else:
                logger.error("No se pudo transcribir ningún segmento")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribiendo por segmentos: {e}")
            return None
    
    def _transcribe_with_pydub(self, audio_path: str) -> Optional[str]:
        """Transcripción usando pydub para procesamiento de audio"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Cargar y procesar con pydub
            audio = AudioSegment.from_file(audio_path)
            
            # Normalizar y convertir a formato estándar
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)
            
            # Exportar como WAV
            audio.export(temp_path, format="wav")
            
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                return None
            
            # Transcribir con parámetros robustos
            result = self.model.transcribe(
                temp_path,
                language='es',
                fp16=False,
                temperature=0.0,
                best_of=1,
                beam_size=1,
                patience=1.0,
                suppress_tokens=[-1],
                without_timestamps=True,
                condition_on_previous_text=False
            )
            return self._format_transcript(result)
            
        except RuntimeError as e:
            if "tensor" in str(e).lower():
                logger.warning(f"Error de tensor con pydub: {e}")
                return self._transcribe_with_safe_mode(audio_path)
            else:
                logger.warning(f"Transcripción con pydub falló: {e}")
                return None
        except Exception as e:
            logger.warning(f"Transcripción con pydub falló: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _transcribe_ultra_basic(self, audio_path: str) -> Optional[str]:
        """Transcripción ultra básica para archivos muy problemáticos"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Conversión ultra básica - solo lo esencial
            cmd = [
                'ffmpeg', 
                '-i', audio_path,
                '-ar', '16000',  # Solo sample rate
                '-ac', '1',       # Solo mono
                '-y', temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Conversión ultra básica falló: {result.stderr}")
                return None
            
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                return None
            
            # Transcribir con parámetros ultra conservadores
            result = self.model.transcribe(
                temp_path, 
                language='es', 
                fp16=False,
                temperature=0.0,
                best_of=1,
                beam_size=1,
                patience=1.0,
                length_penalty=1.0,
                suppress_tokens=[-1],
                without_timestamps=True,
                condition_on_previous_text=False,
                compression_ratio_threshold=2.4,
                no_speech_threshold=0.6
            )
            return self._format_transcript(result)
            
        except RuntimeError as e:
            if "tensor" in str(e).lower():
                logger.warning(f"Error de tensor ultra básica: {e}")
                return self._transcribe_with_safe_mode(audio_path)
            else:
                logger.warning(f"Transcripción ultra básica falló: {e}")
                return None
        except Exception as e:
            logger.warning(f"Transcripción ultra básica falló: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def save_transcript(self, transcript: str, output_path: str) -> bool:
        """
        Guarda la transcripción en un archivo de texto
        
        Args:
            transcript: Texto transcrito
            output_path: Ruta donde guardar el archivo de texto
        
        Returns:
            True si se guardó exitosamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            logger.success("Transcripción guardada", file_info=output_path, 
                          details=f"Caracteres: {len(transcript)}")
            return True
            
        except Exception as e:
            logger.error("Error guardando transcripción", file_info=output_path, 
                        details=f"Error: {e}")
            return False
    
    def process_single_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una sola llamada: descarga audio y transcribe
        
        Args:
            call_data: Diccionario con datos de la llamada
        
        Returns:
            Diccionario con el resultado del procesamiento
        """
        call_id = call_data.get('id')
        logger.info(f"🔍 PASO 5: Procesando llamada individual ID: {call_id}")
        logger.info(f"📊 Datos de la llamada: {call_data.get('user_type', 'N/A')} - {call_data.get('fecha_llamada', 'N/A')}")
        
        result = {
            'call_id': call_id,
            'success': False,
            'audio_path': None,
            'transcript_path': None,
            'transcript': None,
            'error': None
        }
        
        try:
            logger.info(f"🔍 PASO 5.1: Obteniendo URL del audio para ID: {call_id}")
            # Obtener URL del audio (ya viene completa desde la base de datos)
            audio_url = call_data.get('audio_path', '')
            
            # Si la URL no es completa, construirla con AUDIO_BASE_URL
            if not audio_url.startswith(('http://', 'https://')):
                audio_url = f"{self.config.AUDIO_BASE_URL}/{audio_url}"
            
            # Crear estructura de carpetas: año/mes/día
            call_date = call_data.get('fecha_llamada')
            if isinstance(call_date, str):
                call_date = datetime.fromisoformat(call_date.replace('Z', '+00:00'))
            elif isinstance(call_date, datetime):
                pass
            else:
                raise ValueError(f"Formato de fecha no válido: {call_date}")
            
            year = call_date.year
            month = f"{call_date.month:02d}"
            day = f"{call_date.day:02d}"
            
            # Obtener ID de la llamada para crear directorio único
            call_id = call_data.get('id', 'unknown')
            user_type = call_data.get('user_type', 'unknown')
            
            # Crear nombre de archivo truncado y limpio
            original_filename = os.path.basename(call_data.get('audio_path', ''))
            # Limpiar parámetros de URL y truncar nombre
            clean_filename = original_filename.split('?')[0]  # Remover parámetros URL
            filename_without_ext = os.path.splitext(clean_filename)[0]
            audio_extension = os.path.splitext(clean_filename)[1] or '.wav'
            
            # Truncar nombre de archivo a 30 caracteres para evitar nombres muy largos
            truncated_name = filename_without_ext[:30] if len(filename_without_ext) > 30 else filename_without_ext
            
            # Nombres de archivo simplificados
            audio_filename = f"{user_type}_{truncated_name}{audio_extension}"
            text_filename = f"{user_type}_{truncated_name}.txt"
            
            # Rutas de archivos con estructura por llamada
            audio_dir = os.path.join(self.config.AUDIO_DOWNLOAD_PATH, str(year), month, day, f"call_{call_id}")
            text_dir = os.path.join(self.config.TEXT_OUTPUT_PATH, str(year), month, day, f"call_{call_id}")
            
            audio_path = os.path.join(audio_dir, audio_filename)
            text_path = os.path.join(text_dir, text_filename)
            
            # Verificar si ya existe la transcripción
            if os.path.exists(text_path):
                logger.info("Transcripción ya existe", file_info=text_path, details="Omitiendo procesamiento")
                result['success'] = True
                result['transcript_path'] = text_path
                with open(text_path, 'r', encoding='utf-8') as f:
                    result['transcript'] = f.read()
                return result
            
            # Descargar audio
            if not self.download_audio(audio_url, audio_path):
                result['error'] = "Error descargando audio"
                return result
            
            result['audio_path'] = audio_path
            
            # Transcribir audio
            transcript = self.transcribe_audio(audio_path)
            if transcript is None:
                result['error'] = "Error transcribiendo audio"
                return result
            
            result['transcript'] = transcript
            
            # Guardar transcripción
            if not self.save_transcript(transcript, text_path):
                result['error'] = "Error guardando transcripción"
                return result
            
            # Crear archivo de metadatos de la llamada
            self._save_call_metadata(call_data, text_dir, audio_path, text_path)
            
            # Limpiar archivos automáticamente (siempre, exitoso o no)
            self.cleanup_call_files(call_data, success=True)
            
            result['transcript_path'] = text_path
            result['success'] = True
            
        except Exception as e:
            logger.error("Error procesando llamada", details=f"ID: {call_data.get('id')}, Error: {e}")
            result['error'] = str(e)
            
            # Limpiar archivos incluso en caso de error
            self.cleanup_call_files(call_data, success=False)
        
        return result
    
    def _save_call_metadata(self, call_data: Dict[str, Any], text_dir: str, audio_path: str, text_path: str):
        """
        Guarda metadatos de la llamada en un archivo JSON
        """
        try:
            # Convertir fecha a string si es datetime
            fecha_llamada = call_data.get('fecha_llamada')
            if isinstance(fecha_llamada, datetime):
                fecha_llamada = fecha_llamada.isoformat()
            
            metadata = {
                'call_id': call_data.get('id'),
                'user_type': call_data.get('user_type'),
                'fecha_llamada': fecha_llamada,
                'audio_path': audio_path,
                'transcript_path': text_path,
                'processed_at': datetime.now().isoformat(),
                'original_audio_url': call_data.get('audio_path'),
                'agent_id': call_data.get('agent_id'),
                'transcript_length': len(call_data.get('transcript', '')),
                'audio_duration': call_data.get('duration', 'unknown')
            }
            
            metadata_path = os.path.join(text_dir, 'call_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.debug("Metadatos guardados", file_info=metadata_path, 
                        details=f"ID: {call_data.get('id')}")
            
        except Exception as e:
            logger.warning("Error guardando metadatos", details=f"Error: {e}")
    
    def process_calls_batch(self, calls_data: list) -> list:
        """
        Procesa múltiples llamadas en paralelo manteniendo orden cronológico
        
        Args:
            calls_data: Lista de diccionarios con datos de las llamadas (ya ordenada por fecha)
        
        Returns:
            Lista de resultados del procesamiento en orden cronológico
        """
        logger.info("🔍 PASO 4.1: Iniciando procesamiento en lote...")
        logger.info(f"📊 Total de llamadas recibidas: {len(calls_data)}")
        
        # Verificar que las llamadas estén ordenadas por fecha
        logger.info("🔍 PASO 4.2: Verificando orden cronológico de llamadas...")
        self._log_call_order(calls_data[:5])  # Mostrar las primeras 5 para verificación
        
        # Configurar workers según el tipo de procesamiento
        logger.info("🔍 PASO 4.3: Configurando workers de procesamiento...")
        if self.config.CPU_OPTIMIZED:
            max_workers = min(self.config.MAX_CPU_WORKERS, len(calls_data))
            logger.info(f"✅ Procesamiento optimizado para CPU: {max_workers} workers")
            logger.info(f"🔧 Configuración CPU: MAX_CPU_WORKERS={self.config.MAX_CPU_WORKERS}")
        else:
            max_workers = self.config.MAX_CONCURRENT_TRANSCRIPTIONS
            logger.info(f"✅ Procesamiento estándar: {max_workers} workers")
            logger.info(f"🔧 Configuración estándar: MAX_CONCURRENT_TRANSCRIPTIONS={self.config.MAX_CONCURRENT_TRANSCRIPTIONS}")
        
        logger.info(f"🎯 Workers configurados: {max_workers}")
        logger.info(f"🔧 Chunk size: {self.config.CHUNK_SIZE}")
        logger.info(f"🔧 Memoria máxima: {self.config.MAX_MEMORY_USAGE}")
        
        results = []
        
        # Procesar en chunks si está habilitado
        logger.info("🔍 PASO 4.4: Decidiendo estrategia de procesamiento...")
        if self.config.CPU_OPTIMIZED and len(calls_data) > self.config.CHUNK_SIZE:
            logger.info(f"✅ Procesando en chunks de {self.config.CHUNK_SIZE} llamadas")
            logger.info(f"🔧 Total de llamadas: {len(calls_data)}, Chunk size: {self.config.CHUNK_SIZE}")
            logger.info("🚀 Iniciando procesamiento por chunks...")
            return self._process_calls_in_chunks(calls_data, max_workers)
        else:
            logger.info("✅ Procesamiento directo (sin chunks)")
            logger.info(f"🔧 Total de llamadas: {len(calls_data)}, Chunk size: {self.config.CHUNK_SIZE}")
            logger.info("🚀 Iniciando procesamiento directo...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Enviar todas las tareas manteniendo el orden
            future_to_call = {}
            for i, call_data in enumerate(calls_data):
                future = executor.submit(self.process_single_call, call_data)
                future_to_call[future] = (i, call_data)  # Guardar índice para mantener orden
            
            # Crear diccionario para mantener orden de resultados
            results_dict = {}
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_call):
                index, call_data = future_to_call[future]
                try:
                    result = future.result()
                    results_dict[index] = result  # Guardar en posición correcta
                    
                    if result['success']:
                        logger.success("Llamada procesada", details=f"ID: {result['call_id']}, Orden: {index + 1}/{len(calls_data)}")
                    else:
                        logger.error("Error procesando llamada", details=f"ID: {result['call_id']}, Error: {result['error']}")
                        
                except Exception as e:
                    logger.error("Error inesperado", details=f"ID: {call_data.get('id')}, Error: {e}")
                    results_dict[index] = {
                        'call_id': call_data.get('id'),
                        'success': False,
                        'error': str(e)
                    }
            
            # Reconstruir lista en orden cronológico
            for i in range(len(calls_data)):
                if i in results_dict:
                    results.append(results_dict[i])
                else:
                    # Fallback si falta algún resultado
                    results.append({
                        'call_id': calls_data[i].get('id'),
                        'success': False,
                        'error': 'Resultado no encontrado'
                    })
        
        logger.success("Procesamiento completado", details=f"Total: {len(results)}, Exitosas: {sum(1 for r in results if r['success'])}")
        return results
    
    def _log_call_order(self, calls_data: list):
        """Registra el orden de las llamadas para verificación"""
        logger.info("Orden cronológico de llamadas:")
        for i, call in enumerate(calls_data[:5]):
            fecha = call.get('fecha_llamada', 'N/A')
            call_id = call.get('id', 'N/A')
            user_type = call.get('user_type', 'N/A')
            logger.info(f"  {i+1}. ID: {call_id}, Fecha: {fecha}, Tipo: {user_type}")
        
        if len(calls_data) > 5:
            logger.info(f"  ... y {len(calls_data) - 5} llamadas más en orden cronológico")
    
    def _process_calls_in_chunks(self, calls_data: list, max_workers: int) -> list:
        """
        Procesa llamadas en chunks para optimizar el uso de memoria en CPU
        """
        logger.info("🔍 PASO 4.5: Iniciando procesamiento por chunks...")
        chunk_size = self.config.CHUNK_SIZE
        total_chunks = (len(calls_data) + chunk_size - 1) // chunk_size
        
        logger.info(f"📊 Configuración de chunks:")
        logger.info(f"  - Total de llamadas: {len(calls_data)}")
        logger.info(f"  - Tamaño de chunk: {chunk_size}")
        logger.info(f"  - Total de chunks: {total_chunks}")
        logger.info(f"  - Workers por chunk: {max_workers}")
        
        all_results = []
        
        for chunk_idx in range(0, len(calls_data), chunk_size):
            chunk = calls_data[chunk_idx:chunk_idx + chunk_size]
            chunk_num = (chunk_idx // chunk_size) + 1
            
            logger.info(f"🔍 PASO 4.5.{chunk_num}: Procesando chunk {chunk_num}/{total_chunks}")
            logger.info(f"📊 Chunk {chunk_num}: {len(chunk)} llamadas")
            logger.info(f"🔧 Workers para este chunk: {min(max_workers, len(chunk))}")
            
            # Procesar chunk con workers limitados
            chunk_workers = min(max_workers, len(chunk))
            logger.info(f"🚀 Iniciando procesamiento del chunk {chunk_num}...")
            chunk_results = self._process_chunk(chunk, chunk_workers)
            all_results.extend(chunk_results)
            
            logger.success(f"Chunk {chunk_num} completado", 
                         details=f"Exitosas: {sum(1 for r in chunk_results if r['success'])}/{len(chunk)}")
        
        logger.success("Procesamiento en chunks completado", 
                      details=f"Total: {len(all_results)}, Exitosas: {sum(1 for r in all_results if r['success'])}")
        return all_results
    
    def _process_chunk(self, chunk_data: list, max_workers: int) -> list:
        """
        Procesa un chunk de llamadas
        """
        logger.info(f"🔍 PASO 4.6: Procesando chunk con {len(chunk_data)} llamadas")
        logger.info(f"🔧 Workers disponibles: {max_workers}")
        logger.info(f"🚀 Iniciando ThreadPoolExecutor...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            logger.info(f"✅ ThreadPoolExecutor creado con {max_workers} workers")
            
            # Enviar tareas del chunk
            logger.info(f"📤 Enviando {len(chunk_data)} tareas al executor...")
            future_to_call = {}
            for i, call_data in enumerate(chunk_data):
                logger.debug(f"📤 Enviando tarea {i+1}/{len(chunk_data)}: ID {call_data.get('id')}")
                future = executor.submit(self.process_single_call, call_data)
                future_to_call[future] = (i, call_data)
            
            logger.info(f"✅ Todas las tareas enviadas. Esperando resultados...")
            
            # Crear diccionario para mantener orden
            results_dict = {}
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_call):
                index, call_data = future_to_call[future]
                try:
                    result = future.result()
                    results_dict[index] = result
                    
                    if result['success']:
                        logger.debug(f"Llamada {result['call_id']} procesada en chunk")
                    else:
                        logger.warning(f"Error en chunk: {result['call_id']} - {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error inesperado en chunk: {call_data.get('id')} - {e}")
                    results_dict[index] = {
                        'call_id': call_data.get('id'),
                        'success': False,
                        'error': str(e)
                    }
            
            # Reconstruir lista en orden
            for i in range(len(chunk_data)):
                if i in results_dict:
                    results.append(results_dict[i])
                else:
                    results.append({
                        'call_id': chunk_data[i].get('id'),
                        'success': False,
                        'error': 'Resultado no encontrado en chunk'
                    })
        
        return results
    
    def cleanup_call_files(self, call_data: dict, success: bool = True):
        """
        Limpia archivos de una llamada después del procesamiento
        Se ejecuta siempre, exitoso o no
        
        Args:
            call_data: Datos de la llamada
            success: Si el procesamiento fue exitoso (no afecta la limpieza)
        """
        # La limpieza se ejecuta siempre por defecto
        if not self.config.AUTO_CLEANUP:
            logger.debug("Limpieza automática deshabilitada por configuración")
            return
        
        try:
            call_id = call_data.get('id')
            fecha_llamada = call_data.get('fecha_llamada', '')
            
            # Extraer fecha para construir rutas
            if fecha_llamada:
                fecha_obj = datetime.fromisoformat(fecha_llamada.replace('Z', '+00:00'))
                year = fecha_obj.year
                month = f"{fecha_obj.month:02d}"
                day = f"{fecha_obj.day:02d}"
            else:
                logger.warning("No se pudo extraer fecha para limpieza", file_info=f"Call ID: {call_id}")
                return
            
            # Construir rutas de archivos
            audio_dir = os.path.join(self.config.AUDIO_DOWNLOAD_PATH, str(year), month, day, f"call_{call_id}")
            text_dir = os.path.join(self.config.TEXT_OUTPUT_PATH, str(year), month, day, f"call_{call_id}")
            
            # Aplicar delay si está configurado
            if self.config.CLEANUP_DELAY > 0:
                try:
                    delay = int(self.config.CLEANUP_DELAY)
                    logger.debug(f"Esperando {delay}s antes de limpiar", file_info=f"Call ID: {call_id}")
                    time.sleep(delay)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error en delay de limpieza: {e}, continuando sin delay")
            
            # Limpiar archivos de audio si está habilitado
            if self.config.CLEANUP_AUDIO_FILES and os.path.exists(audio_dir):
                self._cleanup_directory(audio_dir, "audio", call_id)
            
            # Limpiar archivos temporales si está habilitado
            if self.config.CLEANUP_TEMP_FILES:
                self._cleanup_temp_files(call_id)
            
            # Limpiar transcripciones solo si no se quiere mantener
            if not self.config.KEEP_TRANSCRIPTS and os.path.exists(text_dir):
                self._cleanup_directory(text_dir, "transcripción", call_id)
            
            logger.success("Limpieza completada", file_info=f"Call ID: {call_id}", 
                         details=f"Audio: {self.config.CLEANUP_AUDIO_FILES}, "
                               f"Temp: {self.config.CLEANUP_TEMP_FILES}, "
                               f"Transcripciones: {not self.config.KEEP_TRANSCRIPTS}")
            
        except Exception as e:
            import traceback
            logger.error("Error en limpieza automática", file_info=f"Call ID: {call_id}", 
                        details=f"Error: {e}, Tipo: {type(e).__name__}")
            logger.debug(f"Traceback completo: {traceback.format_exc()}")
    
    def _cleanup_directory(self, directory: str, file_type: str, call_id: str):
        """
        Limpia un directorio específico
        """
        try:
            if os.path.exists(directory):
                # Contar archivos antes de limpiar
                files_before = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
                
                # Eliminar directorio completo
                shutil.rmtree(directory)
                
                logger.info(f"Directorio {file_type} eliminado", file_info=f"Call ID: {call_id}", 
                          details=f"Archivos eliminados: {files_before}, Directorio: {directory}")
            else:
                logger.debug(f"Directorio {file_type} no existe", file_info=f"Call ID: {call_id}", details=directory)
                
        except Exception as e:
            logger.error(f"Error eliminando directorio {file_type}", file_info=f"Call ID: {call_id}", details=f"Error: {e}")
    
    def _cleanup_temp_files(self, call_id: str):
        """
        Limpia archivos temporales relacionados con la llamada
        """
        try:
            # Buscar archivos temporales en /tmp que contengan el call_id
            temp_patterns = [
                f"/tmp/tmp*{call_id}*",
                f"/tmp/*{call_id}*",
                f"/tmp/tmp*{str(call_id)[:10]}*"  # Buscar por los primeros 10 caracteres del ID
            ]
            
            cleaned_files = 0
            for pattern in temp_patterns:
                temp_files = glob.glob(pattern)
                for temp_file in temp_files:
                    try:
                        if os.path.isfile(temp_file):
                            os.remove(temp_file)
                            cleaned_files += 1
                            logger.debug(f"Archivo temporal eliminado: {temp_file}")
                    except Exception as e:
                        logger.debug(f"No se pudo eliminar archivo temporal: {temp_file} - {e}")
            
            if cleaned_files > 0:
                logger.info("Archivos temporales limpiados", file_info=f"Call ID: {call_id}", 
                          details=f"Archivos eliminados: {cleaned_files}")
            else:
                logger.debug("No se encontraron archivos temporales", file_info=f"Call ID: {call_id}")
                
        except Exception as e:
            logger.error("Error limpiando archivos temporales", file_info=f"Call ID: {call_id}", details=f"Error: {e}")
    
    def get_disk_usage(self, path: str = None) -> dict:
        """
        Obtiene información de uso de disco
        
        Args:
            path: Ruta específica a analizar (por defecto usa las rutas de configuración)
        
        Returns:
            Diccionario con información de uso de disco
        """
        try:
            if path is None:
                audio_path = self.config.AUDIO_DOWNLOAD_PATH
                text_path = self.config.TEXT_OUTPUT_PATH
            else:
                audio_path = text_path = path
            
            usage_info = {}
            
            # Analizar directorio de audios
            if os.path.exists(audio_path):
                audio_size = self._get_directory_size(audio_path)
                usage_info['audio_size_mb'] = round(audio_size / (1024 * 1024), 2)
                usage_info['audio_files'] = self._count_files(audio_path)
            else:
                usage_info['audio_size_mb'] = 0
                usage_info['audio_files'] = 0
            
            # Analizar directorio de transcripciones
            if os.path.exists(text_path):
                text_size = self._get_directory_size(text_path)
                usage_info['text_size_mb'] = round(text_size / (1024 * 1024), 2)
                usage_info['text_files'] = self._count_files(text_path)
            else:
                usage_info['text_size_mb'] = 0
                usage_info['text_files'] = 0
            
            usage_info['total_size_mb'] = usage_info['audio_size_mb'] + usage_info['text_size_mb']
            usage_info['total_files'] = usage_info['audio_files'] + usage_info['text_files']
            
            return usage_info
            
        except Exception as e:
            logger.error("Error obteniendo uso de disco", details=f"Error: {e}")
            return {}
    
    def _get_directory_size(self, directory: str) -> int:
        """Calcula el tamaño total de un directorio"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            logger.debug(f"Error calculando tamaño de directorio: {e}")
        return total_size
    
    def _count_files(self, directory: str) -> int:
        """Cuenta el número de archivos en un directorio"""
        file_count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                file_count += len(filenames)
        except Exception as e:
            logger.debug(f"Error contando archivos: {e}")
        return file_count
