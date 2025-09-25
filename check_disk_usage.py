#!/usr/bin/env python3
"""
Script para verificar el uso de disco del sistema de procesamiento de audio
"""

import os
import sys
import argparse
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio_processor import AudioProcessor, StructuredLogger
from config import Config

def format_size(size_bytes):
    """Convierte bytes a formato legible"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def check_disk_usage(args):
    """Verifica el uso de disco del sistema"""
    logger = StructuredLogger(__name__)
    config = Config()
    
    try:
        # Crear instancia del procesador
        processor = AudioProcessor(config)
        
        # Obtener información de uso de disco
        usage_info = processor.get_disk_usage()
        
        if not usage_info:
            logger.error("No se pudo obtener información de uso de disco")
            return
        
        # Mostrar información general
        logger.info("📊 Información de Uso de Disco")
        print(f"\n{'='*60}")
        print(f"📁 USO DE DISCO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        # Información de audios
        print(f"\n🎵 AUDIOS:")
        print(f"  📊 Tamaño: {usage_info.get('audio_size_mb', 0):.2f} MB")
        print(f"  📄 Archivos: {usage_info.get('audio_files', 0)}")
        print(f"  📍 Directorio: {config.AUDIO_DOWNLOAD_PATH}")
        
        # Información de transcripciones
        print(f"\n📝 TRANSCRIPCIONES:")
        print(f"  📊 Tamaño: {usage_info.get('text_size_mb', 0):.2f} MB")
        print(f"  📄 Archivos: {usage_info.get('text_files', 0)}")
        print(f"  📍 Directorio: {config.TEXT_OUTPUT_PATH}")
        
        # Total
        print(f"\n💾 TOTAL:")
        print(f"  📊 Tamaño Total: {usage_info.get('total_size_mb', 0):.2f} MB")
        print(f"  📄 Archivos Total: {usage_info.get('total_files', 0)}")
        
        # Configuración de limpieza
        print(f"\n🧹 CONFIGURACIÓN DE LIMPIEZA:")
        print(f"  🔄 Limpieza Automática: {'✅ Habilitada' if config.AUTO_CLEANUP else '❌ Deshabilitada'}")
        print(f"  🎵 Limpiar Audios: {'✅ Sí' if config.CLEANUP_AUDIO_FILES else '❌ No'}")
        print(f"  🗑️  Limpiar Temporales: {'✅ Sí' if config.CLEANUP_TEMP_FILES else '❌ No'}")
        print(f"  📝 Mantener Transcripciones: {'✅ Sí' if config.KEEP_TRANSCRIPTS else '❌ No'}")
        print(f"  ⏱️  Delay de Limpieza: {config.CLEANUP_DELAY}s")
        
        # Recomendaciones
        print(f"\n💡 RECOMENDACIONES:")
        total_size_mb = usage_info.get('total_size_mb', 0)
        
        if total_size_mb > 1000:  # Más de 1GB
            print(f"  ⚠️  Uso alto de disco ({total_size_mb:.2f} MB)")
            print(f"  🔧 Considera habilitar limpieza automática")
            print(f"  🗑️  Revisa archivos antiguos que se puedan eliminar")
        elif total_size_mb > 500:  # Más de 500MB
            print(f"  ⚡ Uso moderado de disco ({total_size_mb:.2f} MB)")
            print(f"  🔧 La limpieza automática está funcionando bien")
        else:
            print(f"  ✅ Uso bajo de disco ({total_size_mb:.2f} MB)")
            print(f"  🎉 Sistema optimizado")
        
        # Verificar directorios específicos si se solicita
        if args.detailed:
            print(f"\n🔍 ANÁLISIS DETALLADO:")
            
            # Analizar directorio de audios
            if os.path.exists(config.AUDIO_DOWNLOAD_PATH):
                print(f"\n📁 Audios por fecha:")
                for year in sorted(os.listdir(config.AUDIO_DOWNLOAD_PATH)):
                    year_path = os.path.join(config.AUDIO_DOWNLOAD_PATH, year)
                    if os.path.isdir(year_path):
                        year_size = processor._get_directory_size(year_path)
                        year_files = processor._count_files(year_path)
                        print(f"  📅 {year}: {format_size(year_size)} ({year_files} archivos)")
            
            # Analizar directorio de transcripciones
            if os.path.exists(config.TEXT_OUTPUT_PATH):
                print(f"\n📁 Transcripciones por fecha:")
                for year in sorted(os.listdir(config.TEXT_OUTPUT_PATH)):
                    year_path = os.path.join(config.TEXT_OUTPUT_PATH, year)
                    if os.path.isdir(year_path):
                        year_size = processor._get_directory_size(year_path)
                        year_files = processor._count_files(year_path)
                        print(f"  📅 {year}: {format_size(year_size)} ({year_files} archivos)")
        
        print(f"\n{'='*60}")
        
    except Exception as e:
        logger.error("Error verificando uso de disco", details=f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verificar uso de disco del sistema de procesamiento")
    parser.add_argument("--detailed", action="store_true", help="Mostrar análisis detallado por fecha")
    parser.add_argument("--path", type=str, help="Ruta específica a analizar")
    
    args = parser.parse_args()
    sys.exit(check_disk_usage(args))
