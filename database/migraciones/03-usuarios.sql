-- Para bases creadas antes de la gestión de usuarios (las nuevas ya lo traen en
-- 01-schema.sql). Se aplica una sola vez:
--   docker compose exec -T db psql -U postgres -d asistencia_docentes < database/migraciones/03-usuarios.sql
--
-- Los usuarios que ya existen quedan como administradores. Sus contraseñas, que
-- estaban en texto plano, se cifran solas la primera vez que cada uno ingresa.

ALTER TABLE usuario ADD COLUMN rol VARCHAR(20) NOT NULL DEFAULT 'administrativo';
ALTER TABLE usuario ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE usuario ADD CONSTRAINT usuario_rol_check
    CHECK (rol IN ('administrador', 'administrativo'));
UPDATE usuario SET rol = 'administrador';
CREATE UNIQUE INDEX usuario_nombre_sin_mayusculas_unique ON usuario (LOWER(nombre_usuario));
