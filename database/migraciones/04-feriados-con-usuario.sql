-- Para bases creadas antes de registrar quién carga cada feriado o receso (las
-- nuevas ya lo traen en 01-schema.sql). Se aplica una sola vez:
--   docker compose exec -T db psql -U postgres -d asistencia_docentes < database/migraciones/04-feriados-con-usuario.sql
--
-- Los feriados y recesos que ya existen quedan a nombre del primer administrador.

ALTER TABLE dia_no_laborable ADD COLUMN usuario_id INT NULL;
UPDATE dia_no_laborable
SET usuario_id = (SELECT MIN(id) FROM usuario WHERE rol = 'administrador');
ALTER TABLE dia_no_laborable ALTER COLUMN usuario_id SET NOT NULL;
ALTER TABLE dia_no_laborable ADD CONSTRAINT dia_no_laborable_usuario_id_foreign
    FOREIGN KEY(usuario_id) REFERENCES usuario(id);
