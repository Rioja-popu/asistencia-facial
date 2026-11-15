-- Para bases ya creadas con el schema anterior (sin la columna catedra en jornada).
-- Ejecutar una sola vez; las Jornadas existentes quedan con la catedra vacia.
ALTER TABLE jornada ADD COLUMN IF NOT EXISTS catedra VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE jornada ALTER COLUMN catedra DROP DEFAULT;
