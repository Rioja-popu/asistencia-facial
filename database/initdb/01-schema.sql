CREATE TYPE angulo_foto AS ENUM (
    'frontal',
    'lateral_izquierdo',
    'lateral_derecho'
);
CREATE TABLE alumno(
    id SERIAL NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    dni VARCHAR(255) NOT NULL,
    carrera VARCHAR(255) NOT NULL,
    celular VARCHAR(255) NOT NULL,
    correo_electronico VARCHAR(255) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    anio_ingreso INT NOT NULL,
    domicilio VARCHAR(255) NOT NULL,
    libreta VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE foto_alumno(
    id SERIAL NOT NULL,
    alumno_id INT NOT NULL,
    angulo angulo_foto NOT NULL,
    imagen BYTEA NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE asistencia(
    id SERIAL NOT NULL,
    alumno_id INT NOT NULL,
    entrada TIMESTAMP NOT NULL,
    salida TIMESTAMP NULL,
    jornada_id INT NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE jornada(
    id SERIAL NOT NULL,
    fecha DATE NOT NULL,
    horario_salida TIME NOT NULL,
    horario_entrada TIME NOT NULL,
    usuario_id INT NOT NULL,
    catedra VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
);
CREATE TABLE usuario(
    id SERIAL NOT NULL,
    nombre_usuario VARCHAR(255) NOT NULL UNIQUE, 
    correo_electronico VARCHAR(255) NULL UNIQUE,
    dni VARCHAR(255) NULL UNIQUE,
    cuil VARCHAR(255) NULL UNIQUE,
    contrasenia VARCHAR(255) NOT NULL,
    PRIMARY KEY(id)
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
    jornada ADD CONSTRAINT jornada_usuario_id_foreign FOREIGN KEY(usuario_id) REFERENCES usuario(id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_alumno_id_foreign FOREIGN KEY(alumno_id) REFERENCES alumno(id);
ALTER TABLE
    asistencia ADD CONSTRAINT asistencia_jornada_id_foreign FOREIGN KEY(jornada_id) REFERENCES jornada(id);
ALTER TABLE
    foto_alumno ADD CONSTRAINT foto_alumno_alumno_id_foreign FOREIGN KEY(alumno_id) REFERENCES alumno(id);