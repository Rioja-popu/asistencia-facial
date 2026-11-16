-- Para bases creadas antes de la importación de horarios (las nuevas ya lo traen
-- en 01-schema.sql). Se aplica una sola vez:
--   docker compose exec -T db psql -U postgres -d asistencia_docentes < database/migraciones/01-importacion-horarios.sql

-- Los docentes importados quedan sin DNI ni CUIL hasta que se completan en Docentes
ALTER TABLE docente ALTER COLUMN dni DROP NOT NULL;
ALTER TABLE docente ALTER COLUMN cuil DROP NOT NULL;

-- El cuadro de horarios se arma en módulos de 40 min: un horario dura como mínimo
-- una clase (1 h 20 min) y crece de a un módulo (80, 120, 160...)
ALTER TABLE horario_catedra DROP CONSTRAINT horario_duracion_check;
ALTER TABLE horario_catedra ADD CONSTRAINT horario_duracion_check CHECK (
    hora_fin - hora_inicio >= INTERVAL '80 minutes'
    AND MOD((EXTRACT(EPOCH FROM (hora_fin - hora_inicio)) / 60)::INT, 40) = 0
);
