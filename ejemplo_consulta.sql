-- Ejemplo de consulta SQL para obtener llamadas con URLs completas
-- Ajusta según tu esquema de base de datos

-- Consulta básica por rango de fechas
SELECT 
    id,
    fecha_llamada,
    user_type,
    audio_path,  -- URL completa del archivo
    duracion,
    telefono_origen,
    telefono_destino
FROM llamadas 
WHERE DATE(fecha_llamada) BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY fecha_llamada ASC;

-- Consulta con filtros adicionales
SELECT 
    id,
    fecha_llamada,
    user_type,
    audio_path,
    duracion
FROM llamadas 
WHERE DATE(fecha_llamada) BETWEEN '2024-01-01' AND '2024-01-31'
  AND user_type IN ('cliente', 'agente')
  AND audio_path IS NOT NULL
  AND audio_path != ''
ORDER BY fecha_llamada ASC;

-- Consulta para un día específico
SELECT 
    id,
    fecha_llamada,
    user_type,
    audio_path
FROM llamadas 
WHERE DATE(fecha_llamada) = '2024-01-15'
  AND audio_path LIKE 'https://%'
ORDER BY fecha_llamada ASC;

-- Consulta con validación de URL
SELECT 
    id,
    fecha_llamada,
    user_type,
    audio_path,
    CASE 
        WHEN audio_path LIKE 'https://%' THEN 'URL completa'
        WHEN audio_path LIKE 'http://%' THEN 'URL completa'
        ELSE 'URL relativa'
    END as tipo_url
FROM llamadas 
WHERE DATE(fecha_llamada) BETWEEN '2024-01-01' AND '2024-01-31'
ORDER BY fecha_llamada ASC;
