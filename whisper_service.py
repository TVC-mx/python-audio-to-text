#!/usr/bin/env python3
"""
Servicio de Whisper que mantiene el modelo en memoria
Permite evitar recargar el modelo en cada ejecución
"""

import os
import sys
import time
import signal
import threading
from pathlib import Path
import whisper
import logging
from typing import Optional

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_processor import StructuredLogger, ModelCache

class WhisperService:
    """Servicio que mantiene el modelo Whisper en memoria"""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self.running = False
        self.logger = StructuredLogger("whisper_service")
        
        # Configurar manejo de señales para shutdown graceful
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Manejar señales de terminación"""
        self.logger.info("Recibida señal de terminación", details=f"Señal: {signum}")
        self.stop()
    
    def start(self):
        """Iniciar el servicio"""
        try:
            self.logger.start_process("Iniciando servicio Whisper", details=f"Modelo: {self.model_name}")
            
            # Cargar modelo usando cache global
            model_cache = ModelCache()
            self.model = model_cache.get_model(self.model_name)
            
            self.running = True
            self.logger.success("Servicio Whisper iniciado", details=f"Modelo: {self.model_name}")
            
            # Mantener el servicio corriendo
            self._keep_alive()
            
        except Exception as e:
            self.logger.error("Error iniciando servicio", details=f"Error: {e}")
            sys.exit(1)
    
    def _keep_alive(self):
        """Mantener el servicio vivo"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrupción de teclado recibida")
            self.stop()
    
    def stop(self):
        """Detener el servicio"""
        self.logger.progress("Deteniendo servicio Whisper")
        self.running = False
        
        # Limpiar cache
        model_cache = ModelCache()
        model_cache.clear_cache()
        
        self.logger.success("Servicio Whisper detenido")
        sys.exit(0)
    
    def get_model(self):
        """Obtener el modelo cargado"""
        return self.model

def main():
    """Función principal del servicio"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Servicio Whisper con modelo en memoria")
    parser.add_argument("--model", default="base", help="Modelo Whisper a cargar")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar como daemon")
    
    args = parser.parse_args()
    
    # Crear y ejecutar servicio
    service = WhisperService(args.model)
    
    if args.daemon:
        # Ejecutar como daemon (implementación básica)
        import daemon
        with daemon.DaemonContext():
            service.start()
    else:
        service.start()

if __name__ == "__main__":
    main()
