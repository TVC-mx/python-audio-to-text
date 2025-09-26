#!/usr/bin/env python3
"""
Servicio de transcripción Whisper independiente
Expone una API REST para transcribir archivos de audio
"""

import os
import tempfile
import subprocess
from typing import Optional, Dict, Any
import whisper
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI(
    title="Whisper Transcription Service",
    description="Servicio independiente de transcripción de audio usando Whisper",
    version="1.0.0"
)

# Variables de entorno
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'large')
WHISPER_CACHE_DIR = os.getenv('WHISPER_CACHE_DIR', '/app/models')
PORT = int(os.getenv('PORT', 8000))

# Cache del modelo
model_cache = None

class WhisperService:
    def __init__(self):
        self.model = None
        self.model_name = None
        self._load_model()
    
    def _load_model(self):
        """Carga el modelo de Whisper"""
        global model_cache
        
        if model_cache is None:
            logger.info(f"🔄 Cargando modelo Whisper: {WHISPER_MODEL}")
            logger.info(f"📁 Directorio de cache: {WHISPER_CACHE_DIR}")
            
            try:
                # Configurar directorio de cache
                os.makedirs(WHISPER_CACHE_DIR, exist_ok=True)
                
                # Cargar modelo
                self.model = whisper.load_model(
                    WHISPER_MODEL, 
                    download_root=WHISPER_CACHE_DIR
                )
                self.model_name = WHISPER_MODEL
                model_cache = self
                
                logger.info(f"✅ Modelo {WHISPER_MODEL} cargado exitosamente")
                logger.info(f"📊 Dispositivo: {self.model.device}")
                
            except Exception as e:
                logger.error(f"❌ Error cargando modelo: {e}")
                raise
        else:
            self.model = model_cache.model
            self.model_name = model_cache.model_name
            logger.info("🔄 Usando modelo del cache")
    
    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """Convierte audio a formato WAV estándar"""
        try:
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', 'aresample=resampler=soxr:precision=28:cheby=1,volume=1.0,highpass=f=80,lowpass=f=8000',
                '-acodec', 'pcm_s16le',
                '-ac', '1',
                '-ar', '16000',
                '-sample_fmt', 's16',
                '-f', 'wav',
                '-y', output_path
            ]
            
            logger.info("🔄 Convirtiendo audio...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info("✅ Audio convertido exitosamente")
                return True
            else:
                logger.warning(f"⚠️ Error en conversión: {result.stderr[:100]}")
                return self._fallback_conversion(input_path, output_path)
                
        except Exception as e:
            logger.error(f"❌ Error convirtiendo audio: {e}")
            return False
    
    def _fallback_conversion(self, input_path: str, output_path: str) -> bool:
        """Conversión básica de fallback"""
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
                '-y', output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"❌ Error en conversión de fallback: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str, language: str = 'es') -> Dict[str, Any]:
        """Transcribe un archivo de audio"""
        logger.info(f"🎯 Transcribiendo: {os.path.basename(audio_path)}")
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Convertir audio
            if not self.convert_audio_format(audio_path, temp_path):
                raise HTTPException(status_code=400, detail="Error convirtiendo audio")
            
            # Verificar archivo convertido
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise HTTPException(status_code=400, detail="Archivo convertido está vacío")
            
            # Prompt para mejor formato
            initial_prompt = (
                "Esta es una conversación telefónica transcrita con puntuación completa, "
                "incluyendo puntos, comas, signos de interrogación y exclamación donde corresponda."
            )
            
            # Transcribir con Whisper
            logger.info("🔄 Transcribiendo con Whisper...")
            
            try:
                result = self.model.transcribe(
                    temp_path,
                    language=language,
                    fp16=False,
                    verbose=False,
                    temperature=0.0,
                    best_of=1,
                    beam_size=1,
                    patience=1.0,
                    suppress_tokens=[-1],
                    without_timestamps=False,
                    condition_on_previous_text=True,
                    no_speech_threshold=0.6,
                    compression_ratio_threshold=2.4,
                    initial_prompt=initial_prompt
                )
            except RuntimeError as rt_error:
                error_msg = str(rt_error).lower()
                if any(word in error_msg for word in ["tensor", "reshape", "dimension", "size", "batch"]):
                    logger.warning(f"⚠️ Error de tensor detectado: {rt_error}")
                    logger.info("🔄 Intentando con parámetros conservadores...")
                    
                    # Intentar con parámetros más conservadores
                    result = self.model.transcribe(
                        temp_path,
                        language=language,
                        fp16=False,
                        verbose=False,
                        temperature=0.0,
                        best_of=1,
                        beam_size=1,
                        patience=1.0,
                        suppress_tokens=[-1],
                        without_timestamps=True,
                        condition_on_previous_text=False,
                        no_speech_threshold=0.6,
                        compression_ratio_threshold=2.4,
                        initial_prompt=""
                    )
                else:
                    raise
            
            # Formatear resultado
            transcript = self._format_transcript(result)
            
            return {
                "success": True,
                "transcript": transcript,
                "model": self.model_name,
                "language": language,
                "timestamp": datetime.now().isoformat(),
                "text_length": len(transcript),
                "segments_count": len(result.get("segments", [])) if "segments" in result else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error en transcripción: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _format_transcript(self, result) -> str:
        """Formatea la transcripción para mejor legibilidad"""
        try:
            full_text = result["text"].strip()
            
            # Aplicar formato básico
            formatted_text = self._apply_basic_formatting(full_text)
            
            # Si hay segmentos, usar formato con timestamps
            if "segments" in result and result["segments"]:
                return self._format_with_segments(result, formatted_text)
            else:
                return self._format_simple_text(formatted_text)
                
        except Exception as e:
            logger.error(f"Error formateando transcripción: {e}")
            return result.get("text", "").strip()
    
    def _apply_basic_formatting(self, text: str) -> str:
        """Aplica formato básico al texto"""
        import re
        
        # Limpiar espacios múltiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            return text
        
        # Asegurar que empiece con mayúscula
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Detectar preguntas
        question_words = r'\b(qué|quién|quiénes|cuál|cuáles|cómo|cuándo|dónde|por qué|para qué|cuánto|cuánta|cuántos|cuántas)\b'
        text = re.sub(r'(' + question_words + r'[^.!?]*)', r'\1?', text, flags=re.IGNORECASE)
        
        # Corregir espacios alrededor de puntuación
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
        
        # Asegurar que termina con punto
        if text and not text.rstrip().endswith(('.', '!', '?')):
            text = text.rstrip() + '.'
        
        return text.strip()
    
    def _format_with_segments(self, result, formatted_text: str) -> str:
        """Formatea transcripción con segmentos y timestamps"""
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
            
            if current_start_time is None:
                current_start_time = start_time
            
            current_speaker_text.append(text)
            accumulated_duration = end_time - current_start_time
            
            # Agrupar segmentos cada 30 segundos
            next_segment_gap = 0
            if i + 1 < len(result["segments"]):
                next_segment_gap = result["segments"][i + 1]["start"] - end_time
            
            should_break = (
                accumulated_duration > 30 or
                next_segment_gap > 2 or
                i == len(result["segments"]) - 1
            )
            
            if should_break and current_speaker_text:
                combined_text = ' '.join(current_speaker_text)
                combined_text = self._apply_basic_formatting(combined_text)
                
                start_formatted = self._format_time(current_start_time)
                end_formatted = self._format_time(end_time)
                
                formatted_lines.append(f"[{start_formatted} - {end_formatted}]")
                formatted_lines.append(combined_text)
                formatted_lines.append("")
                
                current_speaker_text = []
                current_start_time = None
                accumulated_duration = 0
        
        # Estadísticas
        formatted_lines.append("=" * 60)
        formatted_lines.append("RESUMEN:")
        formatted_lines.append(f"- Total de caracteres: {len(result['text']):,}")
        formatted_lines.append(f"- Total de palabras: {len(result['text'].split()):,}")
        formatted_lines.append(f"- Duración total: {self._format_time(result['segments'][-1]['end'])}")
        formatted_lines.append(f"- Segmentos procesados: {len(result['segments'])}")
        formatted_lines.append("=" * 60)
        
        return "\n".join(formatted_lines)
    
    def _format_simple_text(self, text: str) -> str:
        """Formatea texto simple"""
        formatted_lines = []
        formatted_lines.append("=" * 60)
        formatted_lines.append("TRANSCRIPCIÓN DE LLAMADA")
        formatted_lines.append("=" * 60)
        formatted_lines.append("")
        formatted_lines.append(text)
        formatted_lines.append("")
        formatted_lines.append("=" * 60)
        formatted_lines.append(f"RESUMEN:")
        formatted_lines.append(f"- Total de caracteres: {len(text):,}")
        formatted_lines.append(f"- Total de palabras: {len(text.split()):,}")
        formatted_lines.append("=" * 60)
        
        return "\n".join(formatted_lines)
    
    def _format_time(self, seconds: float) -> str:
        """Convierte segundos a formato MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

# Inicializar servicio
whisper_service = WhisperService()

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "Whisper Transcription Service",
        "version": "1.0.0",
        "model": whisper_service.model_name,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "model_loaded": whisper_service.model is not None,
        "model_name": whisper_service.model_name,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/transcribe")
async def transcribe_file(
    file: UploadFile = File(...),
    language: str = "es"
):
    """Transcribe un archivo de audio"""
    try:
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Guardar archivo subido
            content = await file.read()
            with open(temp_path, 'wb') as f:
                f.write(content)
            
            # Transcribir
            result = whisper_service.transcribe_audio(temp_path, language)
            
            if result["success"]:
                return JSONResponse(content=result)
            else:
                raise HTTPException(status_code=500, detail=result["error"])
                
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Error procesando archivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe-url")
async def transcribe_url(
    audio_url: str,
    language: str = "es"
):
    """Transcribe un archivo de audio desde URL"""
    try:
        import requests
        
        # Descargar archivo
        response = requests.get(audio_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Guardar archivo descargado
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Transcribir
            result = whisper_service.transcribe_audio(temp_path, language)
            
            if result["success"]:
                return JSONResponse(content=result)
            else:
                raise HTTPException(status_code=500, detail=result["error"])
                
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Error procesando URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info(f"🚀 Iniciando Whisper Service en puerto {PORT}")
    logger.info(f"📊 Modelo: {WHISPER_MODEL}")
    logger.info(f"📁 Cache: {WHISPER_CACHE_DIR}")
    
    uvicorn.run(
        "whisper_service:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
