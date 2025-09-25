import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
from typing import List, Dict, Any
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def connect(self):
        """Establece conexión con la base de datos MySQL"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config.MYSQL_HOST,
                port=self.config.MYSQL_PORT,
                user=self.config.MYSQL_USER,
                password=self.config.MYSQL_PASSWORD,
                database=self.config.MYSQL_DATABASE,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            if self.connection.is_connected():
                logger.info("Conexión exitosa a MySQL")
                return True
        except Error as e:
            logger.error(f"Error conectando a MySQL: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión con la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Conexión MySQL cerrada")
    
    def get_calls_by_date_range(self, start_date: date, end_date: date, query: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene las llamadas en un rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            query: Consulta SQL personalizada (opcional)
        
        Returns:
            Lista de diccionarios con la información de las llamadas
        """
        if not self.connection or not self.connection.is_connected():
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            if query:
                # Si se proporciona una consulta personalizada, la usamos
                cursor.execute(query, (start_date, end_date))
            else:
                # Consulta por defecto - ajustada para tu esquema de base de datos
                # Ordenamiento robusto por fecha y hora para mantener secuencia cronológica
                default_query = """
                SELECT
                    c.id AS id,
                    c.started_at AS fecha_llamada,
                    ca.user_type AS user_type,
                    ca.audio_url AS audio_path,
                    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
                    c.company_id AS telefono_origen,
                    c.branch_id AS telefono_destino,
                    CASE 
                        WHEN c.company_id IS NULL THEN 'No identificado'
                        ELSE 'Identificado'
                    END AS cliente_status,
                    b.name AS sucursal,
                    p.full_name AS atendido_por
                FROM calls c
                LEFT JOIN branches b ON b.id = c.branch_id
                LEFT JOIN users u ON u.id = c.attended_by_employee_id
                LEFT JOIN persons p ON p.id = u.person_id
                LEFT JOIN call_audios ca ON ca.call_id = c.id
                WHERE DATE(c.started_at) BETWEEN %s AND %s
                  AND ca.audio_url IS NOT NULL
                  AND ca.audio_url != ''
                ORDER BY 
                    c.started_at ASC,
                    c.id ASC,
                    ca.user_type ASC
                """
                cursor.execute(default_query, (start_date, end_date))
            
            results = cursor.fetchall()
            cursor.close()
            
            logger.info(f"Se encontraron {len(results)} llamadas entre {start_date} y {end_date}")
            return results
            
        except Error as e:
            logger.error(f"Error ejecutando consulta: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos"""
        try:
            logger.info("🔍 Verificando conexión a la base de datos...")
            logger.info(f"📊 Configuración de conexión:")
            logger.info(f"  - Host: {self.config.MYSQL_HOST}")
            logger.info(f"  - Puerto: {self.config.MYSQL_PORT}")
            logger.info(f"  - Usuario: {self.config.MYSQL_USER}")
            logger.info(f"  - Base de datos: {self.config.MYSQL_DATABASE}")
            
            # Limpiar conexión existente si hay problemas
            if self.connection:
                try:
                    if self.connection.is_connected():
                        # Verificar si hay consultas pendientes
                        cursor = self.connection.cursor()
                        cursor.execute("SELECT 1")
                        cursor.fetchall()  # Consumir cualquier resultado pendiente
                        cursor.close()
                        logger.info("✅ Conexión existente verificada y limpia")
                        return True
                except Error as e:
                    logger.warning(f"⚠️ Conexión existente tiene problemas: {e}")
                    logger.info("🔄 Cerrando conexión problemática...")
                    self.disconnect()
            
            logger.info("🔄 Iniciando nueva conexión...")
            return self.connect()
            
        except Error as e:
            logger.error(f"❌ Error probando conexión: {e}")
            logger.error(f"🔧 Tipo de error: {type(e).__name__}")
            logger.error(f"🔧 Detalles: {str(e)}")
            return False
