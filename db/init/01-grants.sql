-- ============================================================
-- db/init/01-grants.sql
-- ============================================================
-- Se ejecuta automaticamente la PRIMERA vez que el contenedor MySQL
-- inicializa el volumen (no se ejecuta de nuevo en restarts posteriores).
--
-- Concede al usuario `dev` los permisos globales que Prisma necesita
-- para `migrate dev` (crear/destruir su "shadow database").
--
-- IMPORTANTE: este script asume que ya existe el usuario `dev`, creado
-- por las variables MYSQL_USER / MYSQL_PASSWORD del docker-compose.
-- ============================================================

GRANT ALL PRIVILEGES ON *.* TO 'dev'@'%';
FLUSH PRIVILEGES;
