import os
import subprocess
import tempfile
from typing import Optional, Dict, Any, List
import whisper
from datetime import datetime
import warnings
import logging
from logging.handlers import RotatingFileHandler
from pydub import AudioSegment
from config import Config
from custom_logger import CustomLogger
import re

# Configurar warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Logger personalizado
logger = CustomLogger()

# Cache del modelo Whisper
class ModelCache:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.model = None
            self.model_name = None
            self._initialized = True
            
    def get_model(self, model_name: str):
        """Obtener modelo del cache o cargarlo si no existe"""
        logger.info(f"🔍 Verificando cache del modelo...")
        logger.info(f"📊 Estado del cache:")
        logger.info(f"  - Modelo en cache: {self.model_name}")
        logger.info(f"  - Modelo solicitado: {model_name}")
        logger.info(f"  - Cache disponible: {self.model is not None}")
        
        if self.model is None or self.model_name != model_name:
            logger.info(f"🔄 Modelo no está en cache, iniciando descarga...")
            logger.progress("📥 Cargando modelo en cache", details=f"Modelo: {model_name}")
            logger.info(f"⏳ Esto puede tomar varios minutos para modelos grandes...")
            
            # Cargar el modelo
            self.model = whisper.load_model(model_name)
            self.model_name = model_name
            
            logger.success("✅ Modelo cargado en cache", details=f"Modelo: {model_name}")
            logger.info(f"📊 Información del modelo cargado:")
            logger.info(f"  - Modelo: {self.model_name}")
            logger.info(f"  - Objeto en memoria: {self.model is not None}")
            logger.info(f"  - Tipo: {type(self.model)}")
        else:
            logger.debug("🔄 Modelo ya en cache", details=f"Modelo: {model_name}")
        
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
        """Carga el modelo de Whisper con cache persistente"""
        logger.info("=" * 60)
        logger.info("🚀 INICIALIZANDO SISTEMA DE TRANSCRIPCIÓN")
        logger.info("=" * 60)
        
        try:
            logger.info("🚀 Obteniendo modelo del cache global...")
            # Usar cache global del modelo
            self.model = model_cache.get_model(self.config.WHISPER_MODEL)
            logger.success("✅ Modelo Whisper obtenido del cache", details=f"Modelo: {self.config.WHISPER_MODEL}")
            
            # Logs detallados después de cargar el modelo
            logger.info("🔍 Modelo cargado exitosamente")
            logger.info(f"📊 Información del modelo:")
            logger.info(f"  - Modelo activo: {self.config.WHISPER_MODEL}")
            logger.info(f"  - Modelo en memoria: {self.model is not None}")
            
        except Exception as e:
            logger.error("❌ Error cargando modelo Whisper", details=f"Error: {e}")
            raise

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
                logger.success("Audio convertido", file_info=output_path, details="Conversión exitosa")
                return True
            else:
                logger.error("Error en conversión", file_info=input_path, 
                            details=f"Error: {result.stderr[:100]}...")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout en conversión ffmpeg: {input_path}")
            return False
        except Exception as e:
            logger.error(f"Error convirtiendo audio: {e}")
            return False

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe un archivo de audio completo usando Whisper
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Transcripción formateada o None si falla
        """
        logger.info("=" * 60)
        logger.info(f"🎯 INICIANDO TRANSCRIPCIÓN: {os.path.basename(audio_path)}")
        logger.info("=" * 60)
        
        # Crear archivo temporal para conversión
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Convertir audio a formato WAV
            if not self.convert_audio_format(audio_path, temp_path):
                logger.error("No se pudo convertir el audio", file_info=audio_path)
                return None
            
            # Verificar que el archivo convertido existe y tiene contenido
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                logger.error("Archivo convertido está vacío", file_info=audio_path)
                return None
            
            file_size = os.path.getsize(temp_path)
            logger.info(f"📏 Procesando archivo completo (tamaño: {file_size:,} bytes)...")
            
            # Prompt para mejorar formato y puntuación
            initial_prompt = (
                "Esta es una conversación telefónica transcrita con puntuación completa, "
                "incluyendo puntos, comas, signos de interrogación y exclamación donde corresponda. "
                "La transcripción está bien formateada con oraciones completas."
            )
            
            # Transcribir con Whisper
            logger.progress("Transcribiendo con Whisper", file_info=audio_path)
            
            result = self.model.transcribe(
                temp_path,
                language='es',
                fp16=False,
                verbose=False,
                temperature=0.0,
                best_of=1,
                beam_size=1,
                patience=1.0,
                suppress_tokens=[-1],
                without_timestamps=False,  # Para obtener segmentos
                condition_on_previous_text=True,  # Mejor contexto
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4,
                initial_prompt=initial_prompt
            )
            
            # Formatear transcripción
            transcript = self._format_transcript(result)
            
            if transcript:
                logger.success("Transcripción exitosa", file_info=audio_path, 
                              details=f"Caracteres: {len(transcript)}")
                logger.info("=" * 60)
                logger.info(f"✅ FINALIZADA: {os.path.basename(audio_path)}")
                logger.info("=" * 60 + "\n")
                return transcript
            else:
                logger.error("Transcripción no produjo texto", file_info=audio_path)
                return None
                
        except Exception as e:
            logger.error("Error en transcripción", file_info=audio_path, details=f"Error: {e}")
            return None
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)

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

    def get_model_info(self) -> dict:
        """
        Obtiene información sobre el modelo cargado
        
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
            logger.error(f"Error obteniendo información del modelo: {e}")
            return {
                "status": "error",
                "message": f"Error obteniendo información: {str(e)}"
            }
