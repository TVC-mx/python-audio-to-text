#!/usr/bin/env python3
"""
Script para verificar el orden cronológico de las llamadas
"""

import sys
import os
from datetime import datetime
from database import DatabaseManager

def verify_chronological_order(start_date, end_date):
    """Verificar que las llamadas estén en orden cronológico"""
    
    print("🔍 Verificando orden cronológico de llamadas...")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("❌ Error conectando a la base de datos")
        return False
    
    try:
        # Obtener llamadas
        calls_data = db_manager.get_calls_by_date_range(start_date, end_date)
        
        if not calls_data:
            print("❌ No se encontraron llamadas")
            return False
        
        print(f"📊 Total de llamadas: {len(calls_data)}")
        print()
        
        # Verificar orden cronológico
        is_chronological = True
        previous_date = None
        
        print("📅 Orden de llamadas:")
        print("-" * 40)
        
        for i, call in enumerate(calls_data[:10]):  # Mostrar las primeras 10
            fecha_str = call.get('fecha_llamada', 'N/A')
            call_id = call.get('id', 'N/A')
            user_type = call.get('user_type', 'N/A')
            
            try:
                if fecha_str != 'N/A':
                    fecha = datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
                    
                    if previous_date and fecha < previous_date:
                        is_chronological = False
                        print(f"⚠️  ORDEN INCORRECTO en posición {i+1}")
                    
                    previous_date = fecha
                    fecha_formatted = fecha.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    fecha_formatted = 'N/A'
            except Exception as e:
                fecha_formatted = f'Error: {e}'
                is_chronological = False
            
            status = "✅" if is_chronological else "❌"
            print(f"{status} {i+1:3d}. ID: {call_id:8s} | {fecha_formatted} | {user_type}")
        
        if len(calls_data) > 10:
            print(f"    ... y {len(calls_data) - 10} llamadas más")
        
        print()
        print("=" * 60)
        
        if is_chronological:
            print("✅ Las llamadas están en orden cronológico correcto")
        else:
            print("❌ Las llamadas NO están en orden cronológico")
            print("   Esto puede causar problemas en el procesamiento")
        
        return is_chronological
        
    finally:
        db_manager.disconnect()

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python3 verify_chronological_order.py <fecha_inicio> <fecha_fin>")
        print("Ejemplo: python3 verify_chronological_order.py 2024-01-01 2024-01-31")
        sys.exit(1)
    
    start_date = sys.argv[1]
    end_date = sys.argv[2]
    
    try:
        from datetime import datetime
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Formato de fecha inválido. Use YYYY-MM-DD")
        sys.exit(1)
    
    is_chronological = verify_chronological_order(start_date, end_date)
    
    if is_chronological:
        print("\n🎉 El sistema está configurado correctamente para procesamiento cronológico")
        sys.exit(0)
    else:
        print("\n⚠️  Se recomienda revisar la consulta de base de datos")
        sys.exit(1)

if __name__ == "__main__":
    main()
