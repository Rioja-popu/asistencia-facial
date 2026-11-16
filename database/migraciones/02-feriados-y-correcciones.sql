-- Para bases creadas antes de los feriados y la corrección manual de marcaciones
-- (las nuevas ya lo traen en 01-schema.sql). Se aplica una sola vez:
--   docker compose exec -T db psql -U postgres -d asistencia_docentes < database/migraciones/02-feriados-y-correcciones.sql

CREATE TYPE tipo_no_laborable AS ENUM ('feriado', 'receso');
CREATE TABLE dia_no_laborable(
    id SERIAL NOT NULL,
    tipo tipo_no_laborable NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    fecha_desde DATE NOT NULL,
    fecha_hasta DATE NOT NULL,
    PRIMARY KEY(id),
    CONSTRAINT dia_no_laborable_periodo_check CHECK (fecha_hasta >= fecha_desde)
);

ALTER TABLE asistencia ADD COLUMN corregida_por INT NULL;
ALTER TABLE asistencia ADD COLUMN corregida_el TIMESTAMP NULL;
ALTER TABLE asistencia ADD COLUMN motivo_correccion VARCHAR(255) NULL;
ALTER TABLE asistencia ADD CONSTRAINT asistencia_correccion_check CHECK (
    (corregida_por IS NULL AND corregida_el IS NULL AND motivo_correccion IS NULL)
    OR (corregida_por IS NOT NULL AND corregida_el IS NOT NULL AND motivo_correccion IS NOT NULL)
);
ALTER TABLE asistencia ADD CONSTRAINT asistencia_corregida_por_foreign
    FOREIGN KEY(corregida_por) REFERENCES usuario(id);
