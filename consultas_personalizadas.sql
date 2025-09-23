-- Consultas personalizadas para tu esquema de base de datos
-- Basadas en tu estructura: calls, call_audios, branches, users, persons

-- 1. Consulta básica por rango de fechas (la que está en database.py)
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
ORDER BY c.started_at ASC;

-- 2. Solo llamadas de clientes
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND ca.user_type = 'cliente'
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;

-- 3. Solo llamadas de agentes
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND ca.user_type = 'agente'
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;

-- 4. Llamadas de una sucursal específica
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND c.branch_id = 123  -- Cambia por el ID de tu sucursal
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;

-- 5. Llamadas con duración mínima (ej: más de 30 segundos)
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) > 30
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;

-- 6. Llamadas atendidas por un empleado específico
SELECT
    c.id AS id,
    c.started_at AS fecha_llamada,
    ca.user_type AS user_type,
    ca.audio_url AS audio_path,
    TIMESTAMPDIFF(SECOND, c.started_at, c.ended_at) AS duracion,
    c.company_id AS telefono_origen,
    c.branch_id AS telefono_destino,
    b.name AS sucursal,
    p.full_name AS atendido_por
FROM calls c
LEFT JOIN branches b ON b.id = c.branch_id
LEFT JOIN users u ON u.id = c.attended_by_employee_id
LEFT JOIN persons p ON p.id = u.person_id
LEFT JOIN call_audios ca ON ca.call_id = c.id
WHERE DATE(c.started_at) BETWEEN %s AND %s
  AND c.attended_by_employee_id = 456  -- Cambia por el ID del empleado
  AND ca.audio_url IS NOT NULL
  AND ca.audio_url != ''
ORDER BY c.started_at ASC;
