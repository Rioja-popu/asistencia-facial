"""Carreras, cátedras y horarios semanales de los docentes."""

from config.database import consultar, ejecutar


def listar_carreras():
    return consultar("SELECT id, nombre FROM carrera ORDER BY LOWER(nombre);")


def crear_carrera(nombre):
    ejecutar("INSERT INTO carrera (nombre) VALUES (%s);", (nombre,))


def eliminar_carrera(carrera_id):
    ejecutar("DELETE FROM carrera WHERE id = %s;", (carrera_id,))


def listar_catedras():
    return consultar(
        """
        SELECT c.id, c.nombre, c.anio, c.carrera_id, ca.nombre AS carrera
        FROM catedra c
        JOIN carrera ca ON ca.id = c.carrera_id
        ORDER BY LOWER(ca.nombre), c.anio, LOWER(c.nombre);
        """
    )


def crear_catedra(carrera_id, nombre, anio):
    ejecutar(
        "INSERT INTO catedra (carrera_id, nombre, anio) VALUES (%s, %s, %s);",
        (carrera_id, nombre, anio),
    )


def eliminar_catedra(catedra_id):
    ejecutar("DELETE FROM catedra WHERE id = %s;", (catedra_id,))


def listar_horarios(docente_id):
    return consultar(
        """
        SELECT h.id, h.dia_semana, h.hora_inicio, h.hora_fin,
               h.vigente_desde, h.vigente_hasta,
               c.nombre AS catedra, ca.nombre AS carrera
        FROM horario_catedra h
        JOIN catedra c ON c.id = h.catedra_id
        JOIN carrera ca ON ca.id = c.carrera_id
        WHERE h.docente_id = %s
        ORDER BY (h.vigente_hasta IS NOT NULL), h.dia_semana, h.hora_inicio;
        """,
        (docente_id,),
    )


def horarios_superpuestos(docente_id, dia_semana, hora_inicio, hora_fin, desde):
    """Horarios vigentes del docente que se pisan con el bloque que se quiere cargar."""
    return consultar(
        """
        SELECT h.id, c.nombre AS catedra, h.hora_inicio, h.hora_fin
        FROM horario_catedra h
        JOIN catedra c ON c.id = h.catedra_id
        WHERE h.docente_id = %s AND h.dia_semana = %s
          AND h.hora_inicio < %s AND %s < h.hora_fin
          AND (h.vigente_hasta IS NULL OR h.vigente_hasta >= %s);
        """,
        (docente_id, dia_semana, hora_fin, hora_inicio, desde),
    )


def crear_horario(docente_id, catedra_id, dia_semana, hora_inicio, hora_fin, desde):
    ejecutar(
        """
        INSERT INTO horario_catedra
            (docente_id, catedra_id, dia_semana, hora_inicio, hora_fin, vigente_desde)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (docente_id, catedra_id, dia_semana, hora_inicio, hora_fin, desde),
    )


def finalizar_horario(horario_id, hasta):
    """Da de baja un horario sin borrarlo, para conservar los informes anteriores."""
    ejecutar(
        "UPDATE horario_catedra SET vigente_hasta = %s WHERE id = %s;",
        (hasta, horario_id),
    )


def eliminar_horario(horario_id):
    """Sólo es posible si el horario nunca tuvo marcaciones (lo impide la clave foránea)."""
    ejecutar("DELETE FROM horario_catedra WHERE id = %s;", (horario_id,))
