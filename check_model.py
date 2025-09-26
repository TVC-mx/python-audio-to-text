#!/usr/bin/env python3
"""
Script para verificar qué modelo de Whisper está cargado
"""
import json
from audio_processor import AudioProcessor
from config import Config

def main():
    print("=" * 60)
    print("VERIFICACIÓN DE MODELO WHISPER")
    print("=" * 60)
    print()
    
    # Mostrar configuración
    config = Config()
    print("📋 CONFIGURACIÓN:")
    print(f"  - Modelo configurado: {config.WHISPER_MODEL}")
    print(f"  - Cache habilitado: {config.MODEL_CACHE_ENABLED}")
    print(f"  - Modelo persistente: {config.PERSISTENT_MODEL}")
    print()
    
    # Inicializar procesador
    print("🔄 Inicializando procesador de audio...")
    try:
        processor = AudioProcessor()
        print("✅ Procesador inicializado correctamente")
        print()
        
        # Obtener información del modelo
        model_info = processor.get_model_info()
        
        print("🔍 INFORMACIÓN DEL MODELO:")
        print(json.dumps(model_info, indent=2, ensure_ascii=False))
        
        # Verificación adicional
        if model_info.get('status') == 'loaded':
            print()
            print("✅ Modelo cargado exitosamente:")
            print(f"  - Nombre: {model_info.get('model_name')}")
            print(f"  - Tipo: {model_info.get('model_type')}")
            print(f"  - Dispositivo: {model_info.get('device')}")
            print(f"  - Versión Whisper: {model_info.get('whisper_version', 'desconocida')}")
            
            if 'dimensions' in model_info:
                print()
                print("📐 Dimensiones del modelo:")
                for key, value in model_info['dimensions'].items():
                    print(f"  - {key}: {value}")
        else:
            print()
            print("❌ Error al cargar el modelo")
            print(f"  - Mensaje: {model_info.get('message')}")
            
    except Exception as e:
        print(f"❌ Error inicializando procesador: {e}")
    
    print()
    print("=" * 60)
    print("FIN DE VERIFICACIÓN")
    print("=" * 60)

if __name__ == "__main__":
    main()
