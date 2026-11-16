"""Jornadas institucionales y mesas de examen."""

from config.database import consultar, ejecutar


def listar_actividades():
    return consultar(
        """
        SELECT a.id, a.tipo::text AS tipo, a.descripcion, a.fecha,
               a.hora_inicio, a.hora_fin, c.nombre AS catedra,
               COUNT(ad.id) AS participantes
        FROM actividad_especial a
        LEFT JOIN catedra c ON c.id = a.catedra_id
        LEFT JOIN actividad_docente ad ON ad.actividad_id = a.id
        GROUP BY a.id, c.nombre
        ORDER BY a.fecha DESC, a.hora_inicio DESC;
        """
    )


def crear_actividad(tipo, descripcion, fecha, hora_inicio, hora_fin, catedra_id):
    return ejecutar(
        """
        INSERT INTO actividad_especial
            (tipo, descripcion, fecha, hora_inicio, hora_fin, catedra_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (tipo, descripcion, fecha, hora_inicio, hora_fin, catedra_id),
    )["id"]


def eliminar_actividad(actividad_id):
    """Falla si algún participante ya marcó asistencia (lo impide la clave foránea)."""
    ejecutar("DELETE FROM actividad_especial WHERE id = %s;", (actividad_id,))


def listar_participantes(actividad_id):
    return consultar(
        """
        SELECT ad.id, ad.docente_id, ad.rol::text AS rol, d.apellido, d.nombre
        FROM actividad_docente ad
        JOIN docente d ON d.id = ad.docente_id
        WHERE ad.actividad_id = %s
        ORDER BY LOWER(d.apellido), LOWER(d.nombre);
        """,
        (actividad_id,),
    )


def agregar_participante(actividad_id, docente_id, rol):
    ejecutar(
        "INSERT INTO actividad_docente (actividad_id, docente_id, rol) VALUES (%s, %s, %s);",
        (actividad_id, docente_id, rol),
    )


def agregar_todos_los_docentes(actividad_id):
    """Jornada institucional: participan todos los docentes activos."""
    ejecutar(
        """
        INSERT INTO actividad_docente (actividad_id, docente_id)
        SELECT %s, id FROM docente WHERE activo
        ON CONFLICT (actividad_id, docente_id) DO NOTHING;
        """,
        (actividad_id,),
    )


def quitar_participante(participacion_id):
    ejecutar("DELETE FROM actividad_docente WHERE id = %s;", (participacion_id,))
