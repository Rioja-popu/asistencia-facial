-- Sistema de asistencia de docentes - IES N.º 7 Populorum Progressio
-- Esquema de la base asistencia_docentes (rama adaptacion-populorum)

CREATE TYPE angulo_foto AS ENUM (
    'frontal',
    'lateral_izquierdo',
    'lateral_derecho'
);
CREATE TYPE tipo_actividad AS ENUM (
    'jornada_institucional',
    'mesa_examen'
);
CREATE TYPE rol_mesa AS ENUM (
    'presidente',
    'vocal',
    'auxiliar'
);
CREATE TYPE tipo_ausencia AS ENUM (
    'particular',
    'medica'
);
CREATE TYPE estado_ausencia AS ENUM (
    'registrada',
    'pendiente_certificado',
    'justificada',
    'no_justificada'
);

-- Personal administrativo que inicia sesión en el sistema
CREATE TABLE usuario(
    id SERIAL NOT NULL,
    nombre_usuario VARCHAR(255) NOT NULL,
    correo_electronico VARCHAR(255) NULL,
    dni VARCHAR(255) NULL,
    cuil VARCHAR(255) NULL,
    contrasenia VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE docente(
    id SERIAL NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    dni VARCHAR(255) NOT NULL,
    cuil VARCHAR(255) NOT NULL,
    celular VARCHAR(255) NULL,
    correo_electronico VARCHAR(255) NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY(id)
);
CREATE TABLE foto_docente(
    id SERIAL NOT NULL,
    docente_id INT NOT NULL,
    angulo angulo_foto NOT NULL,
    imagen BYTEA NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE carrera(
    id SERIAL NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE catedra(
    id SERIAL NOT NULL,
    carrera_id INT NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    anio INT NOT NULL,
    PRIMARY KEY(id),
    CONSTRAINT catedra_anio_check CHECK (anio BETWEEN 1 AND 6)
);
-- Obligación semanal: qué día y en qué horario un docente dicta una cátedra
CREATE TABLE horario_catedra(
    id SERIAL NOT NULL,
    docente_id INT NOT NULL,
    catedra_id INT NOT NULL,
    dia_semana SMALLINT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    vigente_desde DATE NOT NULL,
    vigente_hasta DATE NULL,
    PRIMARY KEY(id),
    CONSTRAINT horario_dia_semana_check CHECK (dia_semana BETWEEN 1 AND 7),
    -- Cada clase dura 1 h 20 min: el bloque debe medir 80, 160, 240... minutos
    CONSTRAINT horario_duracion_check CHECK (
        hora_fin > hora_inicio
        AND MOD((EXTRACT(EPOCH FROM (hora_fin - hora_inicio)) / 60)::INT, 80) = 0
    ),
    CONSTRAINT horario_vigencia_check CHECK (
        vigente_hasta IS NULL OR vigente_hasta >= vigente_desde
    )
);
-- Jornadas institucionales y mesas de examen (tienen fecha propia)
CREATE TABLE actividad_especial(
    id SERIAL NOT NULL,
    tipo tipo_actividad NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    catedra_id INT NULL,
    PRIMARY KEY(id),
    CONSTRAINT actividad_horario_check CHECK (hora_fin > hora_inicio)
);
CREATE TABLE actividad_docente(
    id SERIAL NOT NULL,
    actividad_id INT NOT NULL,
    docente_id INT NOT NULL,
    rol rol_mesa NULL,
    PRIMARY KEY(id)
);
-- Una fila por docente y por obligación de un día (clase o actividad especial)
CREATE TABLE asistencia(
    id SERIAL NOT NULL,
    docente_id INT NOT NULL,
    fecha DATE NOT NULL,
    horario_catedra_id INT NULL,
    actividad_docente_id INT NULL,
    inicio_previsto TIME NOT NULL,
    fin_previsto TIME NOT NULL,
    entrada TIMESTAMP NOT NULL,
    salida TIMESTAMP NULL,
    tardanza BOOLEAN NOT NULL DEFAULT FALSE,
    salida_anticipada BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY(id),
    CONSTRAINT asistencia_obligacion_check CHECK (
        (horario_catedra_id IS NOT NULL AND actividad_docente_id IS NULL)
        OR (horario_catedra_id IS NULL AND actividad_docente_id IS NOT NULL)
    ),
    CONSTRAINT asistencia_salida_check CHECK (salida IS NULL OR salida >= entrada)
);
-- Particulares y ausencias médicas cargadas por el personal administrativo
CREATE TABLE ausencia(
    id SERIAL NOT NULL,
    docente_id INT NOT NULL,
    fecha DATE NOT NULL,
    tipo tipo_ausencia NOT NULL,
    estado estado_ausencia NOT NULL,
    certificado_presentado_el DATE NULL,
    observacion VARCHAR(255) NULL,
    usuario_id INT NOT NULL,
    PRIMARY KEY(id),
    -- Un particular queda "registrada"; una médica pasa por pendiente/justificada/no justificada
    CONSTRAINT ausencia_estado_check CHECK (
        (tipo = 'particular' AND estado = 'registrada')
        OR (tipo = 'medica' AND estado <> 'registrada')
    )
);

ALTER TABLE
    usuario ADD CONSTRAINT usuario_nombre_usuario_unique UNIQUE(nombre_usuario);
ALTER TABLE
    usuario ADD CONSTRAINT usuario_correo_electronico_unique UNIQUE(correo_electronico);
ALTER TABLE
    usuario ADD CONSTRAINT usuario_dni_unique UNIQUE(dni);
ALTER TABLE
    usuario ADD CONSTRAINT usuario_cuil_unique UNIQUE(cuil);
ALTER TABLE
    docente ADD CONSTRAINT docente_dni_unique UNIQUE(dni);
ALTER TABLE
    docente ADD CONSTRAINT docente_cuil_unique UNIQUE(cuil);
ALTER TABLE
    foto_docente ADD CONSTRAINT foto_docente_angulo_unique UNIQUE(docente_id, angulo);
ALTER TABLE
    carrera ADD CONSTRAINT carrera_nombre_unique UNIQUE(nombre);
ALTER TABLE
    catedra ADD CONSTRAINT catedra_carrera_nombre_unique UNIQUE(carrera_id, nombre);
ALTER TABLE
    actividad_docente ADD CONSTRAINT actividad_docente_unique UNIQUE(actividad_id, docente_id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_clase_unique UNIQUE(fecha, horario_catedra_id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_actividad_unique UNIQUE(fecha, actividad_docente_id);
ALTER TABLE
    ausencia ADD CONSTRAINT ausencia_docente_fecha_unique UNIQUE(docente_id, fecha);

ALTER TABLE
    foto_docente ADD CONSTRAINT foto_docente_docente_id_foreign FOREIGN KEY(docente_id) REFERENCES docente(id) ON DELETE CASCADE;
ALTER TABLE
    catedra ADD CONSTRAINT catedra_carrera_id_foreign FOREIGN KEY(carrera_id) REFERENCES carrera(id);
ALTER TABLE
    horario_catedra ADD CONSTRAINT horario_catedra_docente_id_foreign FOREIGN KEY(docente_id) REFERENCES docente(id);
ALTER TABLE
    horario_catedra ADD CONSTRAINT horario_catedra_catedra_id_foreign FOREIGN KEY(catedra_id) REFERENCES catedra(id);
ALTER TABLE
    actividad_especial ADD CONSTRAINT actividad_especial_catedra_id_foreign FOREIGN KEY(catedra_id) REFERENCES catedra(id);
ALTER TABLE
    actividad_docente ADD CONSTRAINT actividad_docente_actividad_id_foreign FOREIGN KEY(actividad_id) REFERENCES actividad_especial(id) ON DELETE CASCADE;
ALTER TABLE
    actividad_docente ADD CONSTRAINT actividad_docente_docente_id_foreign FOREIGN KEY(docente_id) REFERENCES docente(id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_docente_id_foreign FOREIGN KEY(docente_id) REFERENCES docente(id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_horario_catedra_id_foreign FOREIGN KEY(horario_catedra_id) REFERENCES horario_catedra(id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_actividad_docente_id_foreign FOREIGN KEY(actividad_docente_id) REFERENCES actividad_docente(id);
ALTER TABLE
    ausencia ADD CONSTRAINT ausencia_docente_id_foreign FOREIGN KEY(docente_id) REFERENCES docente(id);
ALTER TABLE
    ausencia ADD CONSTRAINT ausencia_usuario_id_foreign FOREIGN KEY(usuario_id) REFERENCES usuario(id);
