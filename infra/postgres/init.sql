-- Inicialización de bases de datos para microservicios (idempotente)
\set ON_ERROR_STOP on

SELECT 'CREATE DATABASE inventory_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'inventory_db')\gexec

SELECT 'CREATE DATABASE desertbrew_finance'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'desertbrew_finance')\gexec

SELECT 'CREATE DATABASE desertbrew_sales'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'desertbrew_sales')\gexec

SELECT 'CREATE DATABASE desertbrew_security'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'desertbrew_security')\gexec

SELECT 'CREATE DATABASE desertbrew_payroll'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'desertbrew_payroll')\gexec

\echo 'Databases initialized successfully'
