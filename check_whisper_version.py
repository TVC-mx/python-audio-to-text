#!/usr/bin/env python3
"""
Script para verificar la versión de Whisper instalada
"""
import sys

try:
    import whisper
    print(f"✅ Whisper está instalado")
    print(f"📌 Versión: {getattr(whisper, '__version__', 'Versión no disponible')}")
    
    # Información adicional
    print(f"\n📦 Información del paquete:")
    print(f"  - Ubicación: {whisper.__file__}")
    
    # Verificar disponibilidad de modelos
    print(f"\n📂 Modelos disponibles:")
    available_models = whisper.available_models()
    for model in available_models:
        print(f"  - {model}")
    
except ImportError:
    print("❌ Whisper no está instalado")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error verificando Whisper: {e}")
    sys.exit(1)
