#!/usr/bin/env python3
"""
Script principal para procesar llamadas de audio a texto
Conecta a MySQL, descarga audios y los transcribe usando Whisper
"""

import argparse
import sys
from datetime import datetime, date
from typing import List, Dict, Any
import logging
import json
import os

from database import DatabaseManager
from audio_processor import AudioProcessor
from config import Config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def create_logs_directory():
    """Crea el directorio de logs si no existe"""
    os.makedirs('/app/logs', exist_ok=True)

def parse_arguments():
    """Parsea los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Procesar llamadas de audio a texto desde MySQL'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='Fecha de inicio (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='Fecha de fin (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--query',
        type=str,
        help='Consulta SQL personalizada (opcional)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['json', 'csv', 'summary'],
        default='summary',
        help='Formato de salida del reporte'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Solo mostrar qué se procesaría sin ejecutar'
    )
    
    return parser.parse_args()

def validate_date(date_string: str) -> date:
    """Valida y convierte una cadena de fecha"""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Formato de fecha inválido: {date_string}. Use YYYY-MM-DD")

def print_summary(results: List[Dict[str, Any]], start_date: date, end_date: date):
    """Imprime un resumen de los resultados"""
    total_calls = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_calls - successful
    
    print("\n" + "="*60)
    print("RESUMEN DE PROCESAMIENTO")
    print("="*60)
    print(f"Período: {start_date} a {end_date}")
    print(f"Total de llamadas: {total_calls}")
    print(f"Exitosas: {successful}")
    print(f"Fallidas: {failed}")
    print(f"Tasa de éxito: {(successful/total_calls*100):.1f}%" if total_calls > 0 else "0%")
    
    if failed > 0:
        print("\nLlamadas fallidas:")
        for result in results:
            if not result['success']:
                print(f"  - ID {result['call_id']}: {result.get('error', 'Error desconocido')}")
    
    print("="*60)

def save_json_report(results: List[Dict[str, Any]], filename: str):
    """Guarda un reporte en formato JSON"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_calls': len(results),
        'successful': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'results': results
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    logger.info(f"Reporte JSON guardado: {filename}")

def main():
    """Función principal"""
    try:
        # Crear directorio de logs
        create_logs_directory()
        
        # Parsear argumentos
        args = parse_arguments()
        
        # Validar fechas
        start_date = validate_date(args.start_date)
        end_date = validate_date(args.end_date)
        
        if start_date > end_date:
            raise ValueError("La fecha de inicio debe ser anterior a la fecha de fin")
        
        logger.info(f"Iniciando procesamiento desde {start_date} hasta {end_date}")
        
        # Inicializar componentes
        db_manager = DatabaseManager()
        logger.info("🔍 PASO 0: Inicializando procesador de audio...")
        logger.info("⏳ Esto incluye la carga del modelo Whisper (puede tomar varios minutos)...")
        audio_processor = AudioProcessor()
        logger.info("✅ Procesador de audio inicializado exitosamente")
        
        # Logs detallados después de la inicialización
        logger.info("🔍 PASO 0.1: Verificando estado del procesador...")
        logger.info(f"📊 Estado del procesador:")
        logger.info(f"  - Modelo cargado: {audio_processor.model is not None}")
        logger.info(f"  - Configuración CPU: {audio_processor.config.CPU_OPTIMIZED}")
        logger.info(f"  - Workers disponibles: {audio_processor.config.MAX_CPU_WORKERS}")
        logger.info(f"  - Chunk size: {audio_processor.config.CHUNK_SIZE}")
        
        # Conectar a la base de datos
        logger.info("🔍 PASO 0.2: Conectando a la base de datos...")
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a la base de datos")
            logger.error("🔧 Verificar configuración de MySQL en .env")
            sys.exit(1)
        logger.info("✅ Conexión a la base de datos exitosa")
        
        # Obtener llamadas del rango de fechas
        logger.info("🔍 PASO 1: Obteniendo llamadas de la base de datos...")
        logger.info(f"📅 Rango de fechas: {start_date} a {end_date}")
        logger.info(f"🔍 Query personalizada: {args.query if args.query else 'Ninguna'}")
        
        # Verificar conexión a la base de datos
        logger.info("🔍 PASO 2: Verificando conexión a la base de datos...")
        if not db_manager.test_connection():
            logger.error("❌ No se pudo conectar a la base de datos")
            logger.error("🔧 Verificar configuración de MySQL en .env")
            sys.exit(1)
        
        logger.info("✅ Conexión a la base de datos exitosa")
        
        logger.info("🔍 PASO 3: Ejecutando consulta SQL...")
        calls_data = db_manager.get_calls_by_date_range(
            start_date, 
            end_date, 
            args.query
        )
        logger.info(f"📊 Consulta completada. Resultados: {len(calls_data) if calls_data else 0} llamadas")
        
        if not calls_data:
            logger.warning("No se encontraron llamadas en el rango de fechas especificado")
            logger.info("Verificando si hay llamadas en la base de datos...")
            
            # Probar con un rango más amplio para verificar que hay datos
            test_calls = db_manager.get_calls_by_date_range("2020-01-01", "2030-12-31", None)
            if test_calls:
                logger.info(f"Se encontraron {len(test_calls)} llamadas en total en la base de datos")
                logger.info("El problema puede ser que no hay llamadas en el rango específico")
            else:
                logger.error("No se encontraron llamadas en la base de datos")
                logger.error("Verificar configuración de MySQL y datos")
            
            sys.exit(0)
        
        logger.info(f"Se encontraron {len(calls_data)} llamadas para procesar")
        
        # Verificar orden cronológico
        logger.info("Verificando orden cronológico de llamadas...")
        for i, call in enumerate(calls_data[:3]):  # Mostrar las primeras 3
            fecha = call.get('fecha_llamada', 'N/A')
            call_id = call.get('id', 'N/A')
            user_type = call.get('user_type', 'N/A')
            logger.info(f"  {i+1}. ID: {call_id}, Fecha: {fecha}, Tipo: {user_type}")
        
        if len(calls_data) > 3:
            logger.info(f"  ... y {len(calls_data) - 3} llamadas más en orden cronológico")
        
        # Modo dry-run
        if args.dry_run:
            logger.info("MODO DRY-RUN: Solo mostrando qué se procesaría")
            for call in calls_data[:5]:  # Mostrar solo las primeras 5
                print(f"ID: {call.get('id')}, Fecha: {call.get('fecha_llamada')}, "
                      f"User Type: {call.get('user_type')}, Audio: {call.get('audio_path')}")
            if len(calls_data) > 5:
                print(f"... y {len(calls_data) - 5} llamadas más")
            return
        
        # Procesar llamadas
        logger.info("🔍 PASO 4: Iniciando procesamiento de audios...")
        logger.info(f"🎯 Total de llamadas a procesar: {len(calls_data)}")
        logger.info("🔧 Configuración del procesador:")
        logger.info(f"  - Modelo Whisper: {audio_processor.config.WHISPER_MODEL}")
        logger.info(f"  - Workers CPU: {audio_processor.config.MAX_CPU_WORKERS}")
        logger.info(f"  - Limpieza automática: {audio_processor.config.AUTO_CLEANUP}")
        logger.info(f"  - Optimización CPU: {audio_processor.config.CPU_OPTIMIZED}")
        
        logger.info("🚀 Iniciando procesamiento en lote...")
        results = audio_processor.process_calls_batch(calls_data)
        logger.info(f"✅ Procesamiento completado. Resultados: {len(results)} llamadas procesadas")
        
        # Cerrar conexión a la base de datos
        db_manager.disconnect()
        
        # Generar reporte
        if args.output_format == 'json':
            report_filename = f"/app/logs/reporte_{start_date}_{end_date}.json"
            save_json_report(results, report_filename)
        else:
            print_summary(results, start_date, end_date)
        
        # Guardar log de resultados
        log_filename = f"/app/logs/procesamiento_{start_date}_{end_date}.log"
        with open(log_filename, 'w', encoding='utf-8') as f:
            for result in results:
                f.write(f"{json.dumps(result, ensure_ascii=False, default=str)}\n")
        
        logger.info(f"Procesamiento completado. Log guardado en: {log_filename}")
        
        # Código de salida basado en resultados
        successful = sum(1 for r in results if r['success'])
        if successful == len(results):
            sys.exit(0)  # Todo exitoso
        elif successful > 0:
            sys.exit(1)  # Parcialmente exitoso
        else:
            sys.exit(2)  # Todo falló
            
    except KeyboardInterrupt:
        logger.info("Procesamiento interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
