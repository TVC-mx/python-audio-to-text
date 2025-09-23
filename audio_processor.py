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

from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.config = Config()
        self.model = None
        self._load_whisper_model()
    
    def _load_whisper_model(self):
        """Carga el modelo de Whisper"""
        try:
            logger.info(f"Cargando modelo Whisper: {self.config.WHISPER_MODEL}")
            self.model = whisper.load_model(self.config.WHISPER_MODEL)
            logger.info("Modelo Whisper cargado exitosamente")
        except Exception as e:
            logger.error(f"Error cargando modelo Whisper {self.config.WHISPER_MODEL}: {e}")
            logger.info("Intentando con modelo 'tiny' como fallback...")
            try:
                self.model = whisper.load_model("tiny")
                logger.info("Modelo Whisper 'tiny' cargado exitosamente como fallback")
            except Exception as e2:
                logger.error(f"Error cargando modelo Whisper 'tiny': {e2}")
                raise
    
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
            
            logger.info(f"Descargando audio: {audio_url}")
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Audio descargado exitosamente: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error descargando audio {audio_url}: {e}")
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
            
            logger.info(f"Convirtiendo audio con pre-procesamiento agresivo: {input_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"Audio convertido exitosamente con ffmpeg agresivo: {output_path}")
                return True
            else:
                logger.error(f"Error en conversión ffmpeg agresivo: {result.stderr}")
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
            
            # Si hay segmentos disponibles, usarlos para mejor formato
            if "segments" in result and result["segments"]:
                formatted_lines = []
                formatted_lines.append("=" * 60)
                formatted_lines.append("TRANSCRIPCIÓN DE LLAMADA")
                formatted_lines.append("=" * 60)
                formatted_lines.append("")
                
                for i, segment in enumerate(result["segments"], 1):
                    start_time = self._format_time(segment["start"])
                    end_time = self._format_time(segment["end"])
                    text = segment["text"].strip()
                    
                    # Agregar timestamp y texto
                    formatted_lines.append(f"[{start_time} - {end_time}] {text}")
                    
                    # Agregar línea en blanco cada 3 segmentos para mejor legibilidad
                    if i % 3 == 0:
                        formatted_lines.append("")
                
                formatted_lines.append("")
                formatted_lines.append("=" * 60)
                formatted_lines.append(f"FIN DE TRANSCRIPCIÓN - {len(full_text)} caracteres")
                formatted_lines.append("=" * 60)
                
                return "\n".join(formatted_lines)
            else:
                # Si no hay segmentos, formatear el texto completo
                return self._format_simple_text(full_text)
                
        except Exception as e:
            logger.error(f"Error formateando transcripción: {e}")
            # Fallback al texto simple
            return result.get("text", "").strip()
    
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
        
        # Dividir el texto en párrafos más pequeños para mejor legibilidad
        # Buscar puntos, comas y pausas naturales
        import re
        
        # Dividir por puntos, comas y pausas largas
        segments = re.split(r'[.,]\s+', text)
        
        current_paragraph = []
        char_count = 0
        
        for segment in segments:
            if segment.strip():
                current_paragraph.append(segment.strip())
                char_count += len(segment)
                
                # Crear párrafo cada 200 caracteres aproximadamente
                if char_count > 200:
                    paragraph_text = '. '.join(current_paragraph)
                    if not paragraph_text.endswith('.'):
                        paragraph_text += '.'
                    
                    formatted_lines.append(paragraph_text)
                    formatted_lines.append("")  # Línea en blanco
                    
                    current_paragraph = []
                    char_count = 0
        
        # Agregar el último párrafo si queda algo
        if current_paragraph:
            paragraph_text = '. '.join(current_paragraph)
            if not paragraph_text.endswith('.'):
                paragraph_text += '.'
            formatted_lines.append(paragraph_text)
            formatted_lines.append("")
        
        formatted_lines.append("=" * 60)
        formatted_lines.append(f"FIN DE TRANSCRIPCIÓN - {len(text)} caracteres")
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
                logger.error(f"Archivo de audio no encontrado: {audio_path}")
                return None
            
            logger.info(f"Transcribiendo audio: {audio_path}")
            
            # Siempre convertir el audio primero para archivos MP3 problemáticos
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Convertir audio con pre-procesamiento agresivo
                if not self.convert_audio_format(audio_path, temp_path):
                    logger.error(f"No se pudo convertir el archivo de audio: {audio_path}")
                    return None
                
                # Verificar que el archivo convertido existe y tiene contenido
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    logger.error(f"Archivo convertido vacío o no existe: {temp_path}")
                    return None
                
                # Transcribir con el archivo convertido
                result = self.model.transcribe(
                    temp_path,
                    language='es',  # Español
                    fp16=False,  # Usar fp32 para mejor compatibilidad
                    verbose=False,
                    # Parámetros adicionales para mejor compatibilidad
                    condition_on_previous_text=False,
                    initial_prompt=None
                )
                
                # Formatear la transcripción para mejor legibilidad
                transcript = self._format_transcript(result)
                logger.info(f"Transcripción completada: {len(transcript)} caracteres")
                
                # Limpiar archivo temporal
                os.unlink(temp_path)
                return transcript
                
            except Exception as e:
                logger.error(f"Error en transcripción con archivo convertido: {e}")
                # Limpiar archivo temporal
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
            
        except Exception as e:
            logger.error(f"Error transcribiendo audio {audio_path}: {e}")
            return None
    
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
            
            logger.info(f"Transcripción guardada: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando transcripción {output_path}: {e}")
            return False
    
    def process_single_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una sola llamada: descarga audio y transcribe
        
        Args:
            call_data: Diccionario con datos de la llamada
        
        Returns:
            Diccionario con el resultado del procesamiento
        """
        result = {
            'call_id': call_data.get('id'),
            'success': False,
            'audio_path': None,
            'transcript_path': None,
            'transcript': None,
            'error': None
        }
        
        try:
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
            
            # Crear nombre del archivo con prefijo de user_type
            user_type = call_data.get('user_type', 'unknown')
            original_filename = os.path.basename(call_data.get('audio_path', ''))
            filename_without_ext = os.path.splitext(original_filename)[0]
            audio_extension = os.path.splitext(original_filename)[1] or '.wav'
            
            audio_filename = f"{user_type}_{filename_without_ext}{audio_extension}"
            text_filename = f"{user_type}_{filename_without_ext}.txt"
            
            # Rutas de archivos
            audio_dir = os.path.join(self.config.AUDIO_DOWNLOAD_PATH, str(year), month, day)
            text_dir = os.path.join(self.config.TEXT_OUTPUT_PATH, str(year), month, day)
            
            audio_path = os.path.join(audio_dir, audio_filename)
            text_path = os.path.join(text_dir, text_filename)
            
            # Verificar si ya existe la transcripción
            if os.path.exists(text_path):
                logger.info(f"Transcripción ya existe, omitiendo: {text_path}")
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
            
            result['transcript_path'] = text_path
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Error procesando llamada {call_data.get('id')}: {e}")
            result['error'] = str(e)
        
        return result
    
    def process_calls_batch(self, calls_data: list) -> list:
        """
        Procesa múltiples llamadas en paralelo
        
        Args:
            calls_data: Lista de diccionarios con datos de las llamadas
        
        Returns:
            Lista de resultados del procesamiento
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.MAX_CONCURRENT_TRANSCRIPTIONS) as executor:
            # Enviar todas las tareas
            future_to_call = {
                executor.submit(self.process_single_call, call_data): call_data 
                for call_data in calls_data
            }
            
            # Procesar resultados conforme se completan
            for future in as_completed(future_to_call):
                call_data = future_to_call[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        logger.info(f"Llamada {result['call_id']} procesada exitosamente")
                    else:
                        logger.error(f"Error procesando llamada {result['call_id']}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error inesperado procesando llamada {call_data.get('id')}: {e}")
                    results.append({
                        'call_id': call_data.get('id'),
                        'success': False,
                        'error': str(e)
                    })
        
        return results
