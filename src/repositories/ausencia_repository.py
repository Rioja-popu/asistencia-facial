"""Particulares y ausencias médicas cargadas por el personal administrativo."""

from config.database import consultar, ejecutar

PARTICULARES_POR_ANIO = 6


def listar_ausencias(docente_id=None, solo_pendientes=False):
    condiciones, params = [], []
    if docente_id is not None:
        condiciones.append("au.docente_id = %s")
        params.append(docente_id)
    if solo_pendientes:
        condiciones.append("au.estado = 'pendiente_certificado'")
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    return consultar(
        f"""
        SELECT au.id, au.docente_id, au.fecha, au.tipo::text AS tipo,
               au.estado::text AS estado, au.certificado_presentado_el,
               au.observacion, d.apellido, d.nombre, u.nombre_usuario
        FROM ausencia au
        JOIN docente d ON d.id = au.docente_id
        JOIN usuario u ON u.id = au.usuario_id
        {where}
        ORDER BY au.fecha DESC, LOWER(d.apellido);
        """,
        params,
    )


def obtener_ausencias(docente_id, desde, hasta):
    """Ausencias del docente en el período, indexadas por fecha."""
    filas = consultar(
        """
        SELECT fecha, tipo::text AS tipo, estado::text AS estado
        FROM ausencia
        WHERE docente_id = %s AND fecha BETWEEN %s AND %s;
        """,
        (docente_id, desde, hasta),
    )
    return {fila["fecha"]: fila for fila in filas}


def contar_particulares(docente_id, anio):
    return consultar(
        """
        SELECT COUNT(*) AS cantidad
        FROM ausencia
        WHERE docente_id = %s AND tipo = 'particular'
          AND EXTRACT(YEAR FROM fecha) = %s;
        """,
        (docente_id, anio),
    )[0]["cantidad"]


def registrar_ausencia(docente_id, fecha, tipo, observacion, usuario_id):
    """Carga un particular o una ausencia médica.

    Lanza ValueError si el docente ya usó sus 6 particulares del año
    o si ya tiene una ausencia cargada ese día.
    """
    if consultar(
        "SELECT 1 FROM ausencia WHERE docente_id = %s AND fecha = %s;",
        (docente_id, fecha),
    ):
        raise ValueError("El docente ya tiene una ausencia cargada para esa fecha.")
    if tipo == "particular":
        usados = contar_particulares(docente_id, fecha.year)
        if usados >= PARTICULARES_POR_ANIO:
            raise ValueError(
                f"El docente ya utilizó los {PARTICULARES_POR_ANIO} particulares "
                f"del año {fecha.year}."
            )
        estado = "registrada"
    else:
        estado = "pendiente_certificado"
    ejecutar(
        """
        INSERT INTO ausencia (docente_id, fecha, tipo, estado, observacion, usuario_id)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (docente_id, fecha, tipo, estado, observacion or None, usuario_id),
    )


def resolver_medica(ausencia_id, justificada, fecha_certificado=None):
    """Cierra el seguimiento de una ausencia médica pendiente."""
    ejecutar(
        """
        UPDATE ausencia
        SET estado = %s, certificado_presentado_el = %s
        WHERE id = %s AND tipo = 'medica';
        """,
        (
            "justificada" if justificada else "no_justificada",
            fecha_certificado if justificada else None,
            ausencia_id,
        ),
    )


def eliminar_ausencia(ausencia_id):
    ejecutar("DELETE FROM ausencia WHERE id = %s;", (ausencia_id,))
