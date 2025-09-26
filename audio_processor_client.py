import os
import requests
import tempfile
from typing import Optional, Dict, Any, List
from datetime import datetime
from config import Config
from custom_logger import CustomLogger
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing
from tqdm import tqdm

# Logger personalizado
logger = CustomLogger()


class AudioProcessorClient:
    def __init__(self):
        self.config = Config()
        self.whisper_service_url = os.getenv('WHISPER_SERVICE_URL', 'http://localhost:8000')
        self._test_connection()
    
    def _test_connection(self):
        """Verifica que el servicio de Whisper esté disponible"""
        try:
            response = requests.get(f"{self.whisper_service_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.success("✅ Conectado al servicio de Whisper", 
                             details=f"Modelo: {health_data.get('model_name', 'unknown')}")
            else:
                raise Exception(f"Servicio no saludable: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ No se pudo conectar al servicio de Whisper: {e}")
            logger.error(f"🔧 Verificar que el servicio esté ejecutándose en: {self.whisper_service_url}")
            raise

    def transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe un archivo de audio usando el servicio de Whisper
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Transcripción formateada o None si falla
        """
        logger.info("=" * 60)
        logger.info(f"🎯 INICIANDO TRANSCRIPCIÓN: {os.path.basename(audio_path)}")
        logger.info("=" * 60)
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(audio_path):
                logger.error("Archivo de audio no encontrado", file_info=audio_path)
                return None
            
            # Enviar archivo al servicio de Whisper
            with open(audio_path, 'rb') as audio_file:
                files = {'file': (os.path.basename(audio_path), audio_file, 'audio/mpeg')}
                data = {'language': 'es'}
                
                logger.progress("Transcribiendo con servicio de Whisper", file_info=audio_path)
                
                response = requests.post(
                    f"{self.whisper_service_url}/transcribe",
                    files=files,
                    data=data,
                    timeout=300  # 5 minutos timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        transcript = result.get('transcript', '')
                        logger.success("Transcripción exitosa", file_info=audio_path, 
                                      details=f"Caracteres: {len(transcript)}")
                        logger.info("=" * 60)
                        logger.info(f"✅ FINALIZADA: {os.path.basename(audio_path)}")
                        logger.info("=" * 60 + "\n")
                        return transcript
                    else:
                        logger.error("Error en transcripción", file_info=audio_path, 
                                   details=result.get('error', 'Error desconocido'))
                        return None
                else:
                    logger.error("Error del servicio", file_info=audio_path, 
                               details=f"Status: {response.status_code}, Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error("Error en transcripción", file_info=audio_path, details=f"Error: {e}")
            return None

    def transcribe_audio_from_url(self, audio_url: str) -> Optional[str]:
        """
        Transcribe un archivo de audio desde URL usando el servicio de Whisper
        
        Args:
            audio_url: URL del archivo de audio
        
        Returns:
            Transcripción formateada o None si falla
        """
        logger.info("=" * 60)
        logger.info(f"🎯 TRANSCRIBIENDO DESDE URL: {audio_url}")
        logger.info("=" * 60)
        
        try:
            data = {
                'audio_url': audio_url,
                'language': 'es'
            }
            
            logger.progress("Transcribiendo URL con servicio de Whisper", file_info=audio_url)
            
            response = requests.post(
                f"{self.whisper_service_url}/transcribe-url",
                json=data,
                timeout=300  # 5 minutos timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    transcript = result.get('transcript', '')
                    logger.success("Transcripción exitosa", file_info=audio_url, 
                                  details=f"Caracteres: {len(transcript)}")
                    logger.info("=" * 60)
                    logger.info(f"✅ FINALIZADA: {audio_url}")
                    logger.info("=" * 60 + "\n")
                    return transcript
                else:
                    logger.error("Error en transcripción", file_info=audio_url, 
                               details=result.get('error', 'Error desconocido'))
                    return None
            else:
                logger.error("Error del servicio", file_info=audio_url, 
                           details=f"Status: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error("Error en transcripción", file_info=audio_url, details=f"Error: {e}")
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
            
            logger.success("Transcripción guardada", file_info=output_path, 
                          details=f"Caracteres: {len(transcript)}")
            return True
        except Exception as e:
            logger.error("Error guardando transcripción", file_info=output_path, 
                        details=f"Error: {e}")
            return False

    def download_audio_file(self, audio_url: str, local_path: str) -> bool:
        """
        Descarga un archivo de audio desde una URL
        
        Args:
            audio_url: URL del archivo de audio
            local_path: Ruta local donde guardar el archivo
        
        Returns:
            True si se descargó exitosamente, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Descargar archivo
            logger.progress("Descargando audio", file_info=audio_url)
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Guardar archivo
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.success("Audio descargado", file_info=local_path)
            return True
            
        except Exception as e:
            logger.error(f"Error descargando audio: {e}", file_info=audio_url)
            return False

    def process_single_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una sola llamada: descarga y transcribe
        
        Args:
            call_data: Diccionario con información de la llamada
        
        Returns:
            Diccionario con resultado del procesamiento
        """
        call_id = call_data.get('id', 'unknown')
        audio_path = call_data.get('audio_path', '')
        
        result = {
            'call_id': call_id,
            'success': False,
            'transcript_path': None,
            'error': None
        }
        
        try:
            # Construir rutas
            audio_filename = os.path.basename(audio_path)
            
            # Manejar fecha de llamada
            fecha_llamada = call_data.get('fecha_llamada')
            if isinstance(fecha_llamada, str):
                fecha_llamada = datetime.strptime(fecha_llamada, '%Y-%m-%d')
            elif not fecha_llamada:
                fecha_llamada = datetime.now()
            
            fecha_str = fecha_llamada.strftime('%Y/%m/%d')
            
            # Rutas locales
            local_audio_path = os.path.join(
                self.config.AUDIO_DOWNLOAD_PATH,
                fecha_str,
                audio_filename
            )
            
            transcript_path = os.path.join(
                self.config.TEXT_OUTPUT_PATH,
                fecha_str,
                f"{os.path.splitext(audio_filename)[0]}.txt"
            )
            
            # Descargar audio si no existe
            if not os.path.exists(local_audio_path):
                audio_url = f"{self.config.AUDIO_BASE_URL}/{audio_path}"
                if not self.download_audio_file(audio_url, local_audio_path):
                    result['error'] = "Error descargando audio"
                    return result
            
            # Transcribir audio usando el servicio
            transcript = self.transcribe_audio(local_audio_path)
            if transcript:
                # Guardar transcripción
                if self.save_transcript(transcript, transcript_path):
                    result['success'] = True
                    result['transcript_path'] = transcript_path
                else:
                    result['error'] = "Error guardando transcripción"
            else:
                result['error'] = "Error en transcripción"
            
            # Limpiar archivos si está configurado
            if self.config.AUTO_CLEANUP and self.config.CLEANUP_AUDIO_FILES:
                try:
                    os.remove(local_audio_path)
                    logger.debug(f"Archivo de audio eliminado: {local_audio_path}")
                except:
                    pass
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error procesando llamada {call_id}: {e}")
            return result

    def process_calls_batch(self, calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa un lote de llamadas, con opción de procesamiento paralelo
        
        Args:
            calls_data: Lista de diccionarios con información de llamadas
        
        Returns:
            Lista de resultados del procesamiento
        """
        total_calls = len(calls_data)
        logger.info(f"🎯 Iniciando procesamiento de {total_calls} llamadas")
        
        # Determinar si usar procesamiento paralelo
        use_parallel = (
            self.config.ENABLE_PARALLEL_TRANSCRIPTIONS and 
            total_calls > 1 and
            self.config.MAX_CPU_WORKERS > 1
        )
        
        if use_parallel:
            return self._process_calls_parallel(calls_data)
        else:
            return self._process_calls_sequential(calls_data)

    def _process_calls_sequential(self, calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa llamadas de forma secuencial
        """
        results = []
        
        with tqdm(total=len(calls_data), desc="Procesando llamadas", unit="llamada") as pbar:
            for i, call_data in enumerate(calls_data):
                logger.info(f"📞 Procesando llamada {i+1}/{len(calls_data)}")
                result = self.process_single_call(call_data)
                results.append(result)
                
                # Actualizar barra de progreso
                pbar.update(1)
                
                # Log del resultado
                if result['success']:
                    logger.success(f"✅ Llamada {result['call_id']} procesada exitosamente")
                else:
                    logger.error(f"❌ Error en llamada {result['call_id']}: {result['error']}")
        
        return results

    def _process_calls_parallel(self, calls_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Procesa llamadas en paralelo usando ThreadPoolExecutor
        """
        max_workers = min(self.config.MAX_CPU_WORKERS, len(calls_data))
        logger.info(f"🚀 Procesamiento paralelo con {max_workers} workers")
        logger.info("📡 Usando servicio de Whisper independiente")
        
        results = []
        
        # Usar ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear futures para cada llamada
            future_to_call = {
                executor.submit(self.process_single_call, call_data): call_data
                for call_data in calls_data
            }
            
            # Procesar resultados conforme se completan
            with tqdm(total=len(calls_data), desc="Procesando llamadas", unit="llamada") as pbar:
                for future in as_completed(future_to_call):
                    call_data = future_to_call[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Log del resultado
                        if result['success']:
                            logger.success(f"✅ Llamada {result['call_id']} procesada")
                        else:
                            logger.error(f"❌ Error en llamada {result['call_id']}: {result['error']}")
                        
                    except Exception as e:
                        logger.error(f"❌ Excepción procesando llamada: {e}")
                        results.append({
                            'call_id': call_data.get('id', 'unknown'),
                            'success': False,
                            'transcript_path': None,
                            'error': str(e)
                        })
                    
                    finally:
                        pbar.update(1)
        
        return results

    def get_service_info(self) -> Dict[str, Any]:
        """
        Obtiene información del servicio de Whisper
        
        Returns:
            Diccionario con información del servicio
        """
        try:
            response = requests.get(f"{self.whisper_service_url}/health", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "status": "error",
                    "message": f"Servicio no disponible: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error conectando al servicio: {str(e)}"
            }
