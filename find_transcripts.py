#!/usr/bin/env python3
"""
Utilidad para buscar y navegar transcripciones por llamada
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

def find_transcripts_by_date(year, month, day):
    """Buscar transcripciones por fecha"""
    base_path = Path("./textos")
    date_path = base_path / str(year) / f"{month:02d}" / f"{day:02d}"
    
    if not date_path.exists():
        print(f"❌ No se encontraron transcripciones para {year}-{month:02d}-{day:02d}")
        return []
    
    calls = []
    for call_dir in date_path.iterdir():
        if call_dir.is_dir() and call_dir.name.startswith('call_'):
            call_id = call_dir.name.replace('call_', '')
            metadata_file = call_dir / 'call_metadata.json'
            
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                calls.append(metadata)
            else:
                # Información básica si no hay metadatos
                calls.append({
                    'call_id': call_id,
                    'call_dir': str(call_dir),
                    'metadata_file': 'No disponible'
                })
    
    return calls

def find_transcript_by_call_id(call_id):
    """Buscar transcripción por ID de llamada"""
    base_path = Path("./textos")
    
    for year_dir in base_path.iterdir():
        if not year_dir.is_dir():
            continue
            
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                    
                call_dir = day_dir / f"call_{call_id}"
                if call_dir.exists():
                    return call_dir
    
    return None

def list_recent_transcripts(days=7):
    """Listar transcripciones recientes"""
    base_path = Path("./textos")
    recent_calls = []
    
    for year_dir in sorted(base_path.iterdir(), reverse=True):
        if not year_dir.is_dir():
            continue
            
        for month_dir in sorted(year_dir.iterdir(), reverse=True):
            if not month_dir.is_dir():
                continue
                
            for day_dir in sorted(month_dir.iterdir(), reverse=True):
                if not day_dir.is_dir():
                    continue
                    
                for call_dir in day_dir.iterdir():
                    if call_dir.is_dir() and call_dir.name.startswith('call_'):
                        metadata_file = call_dir / 'call_metadata.json'
                        if metadata_file.exists():
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                            recent_calls.append(metadata)
                            
                            if len(recent_calls) >= 20:  # Limitar a 20 resultados
                                return recent_calls
    
    return recent_calls

def show_transcript_content(call_id):
    """Mostrar contenido de una transcripción específica"""
    call_dir = find_transcript_by_call_id(call_id)
    if not call_dir:
        print(f"❌ No se encontró transcripción para call_id: {call_id}")
        return
    
    # Buscar archivos de transcripción
    transcript_files = list(call_dir.glob("*.txt"))
    if not transcript_files:
        print(f"❌ No se encontraron archivos de transcripción en {call_dir}")
        return
    
    print(f"📁 Transcripción encontrada en: {call_dir}")
    print("=" * 60)
    
    for transcript_file in transcript_files:
        print(f"\n📄 Archivo: {transcript_file.name}")
        print("-" * 40)
        
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            print(f"❌ Error leyendo archivo: {e}")

def main():
    parser = argparse.ArgumentParser(description="Buscar transcripciones por llamada")
    parser.add_argument("--date", help="Buscar por fecha (YYYY-MM-DD)")
    parser.add_argument("--call-id", help="Buscar por ID de llamada")
    parser.add_argument("--recent", type=int, default=7, help="Mostrar transcripciones recientes (días)")
    parser.add_argument("--show-content", help="Mostrar contenido de transcripción por call_id")
    
    args = parser.parse_args()
    
    if args.date:
        try:
            date_obj = datetime.strptime(args.date, "%Y-%m-%d")
            calls = find_transcripts_by_date(date_obj.year, date_obj.month, date_obj.day)
            
            print(f"📅 Transcripciones para {args.date}:")
            print("=" * 50)
            
            if not calls:
                print("❌ No se encontraron transcripciones")
            else:
                for call in calls:
                    print(f"📞 Call ID: {call.get('call_id', 'N/A')}")
                    print(f"👤 Tipo: {call.get('user_type', 'N/A')}")
                    print(f"📁 Directorio: {call.get('call_dir', 'N/A')}")
                    print("-" * 30)
        
        except ValueError:
            print("❌ Formato de fecha inválido. Use YYYY-MM-DD")
    
    elif args.call_id:
        call_dir = find_transcript_by_call_id(args.call_id)
        if call_dir:
            print(f"✅ Transcripción encontrada: {call_dir}")
        else:
            print(f"❌ No se encontró transcripción para call_id: {args.call_id}")
    
    elif args.show_content:
        show_transcript_content(args.show_content)
    
    else:
        # Mostrar transcripciones recientes por defecto
        calls = list_recent_transcripts(args.recent)
        
        print(f"📅 Transcripciones recientes (últimos {args.recent} días):")
        print("=" * 60)
        
        if not calls:
            print("❌ No se encontraron transcripciones recientes")
        else:
            for call in calls[:10]:  # Mostrar solo las 10 más recientes
                print(f"📞 Call ID: {call.get('call_id', 'N/A')}")
                print(f"👤 Tipo: {call.get('user_type', 'N/A')}")
                print(f"📅 Fecha: {call.get('fecha_llamada', 'N/A')}")
                print(f"📁 Directorio: {call.get('call_dir', 'N/A')}")
                print("-" * 40)

if __name__ == "__main__":
    main()
