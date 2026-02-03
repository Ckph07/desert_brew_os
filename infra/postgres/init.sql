-- Inicialización de bases de datos para Inventory y Finance
CREATE DATABASE IF NOT EXISTS finance_db;

-- Crear usuario específico si es necesario
-- (El usuario 'desertbrew' ya existe vía env vars)

-- Confirmar creación
\echo 'Databases initialized successfully'
