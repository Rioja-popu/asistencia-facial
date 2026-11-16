"""Obligaciones horarias de un docente y sus marcaciones."""

from config.database import consultar, ejecutar, get_connection

ROLES = {"presidente": "Presidente", "vocal": "Vocal", "auxiliar": "Auxiliar"}
TIPOS_ACTIVIDAD = {
    "jornada_institucional": "Jornada institucional",
    "mesa_examen": "Mesa de examen",
}


def obtener_obligaciones(docente_id, desde, hasta=None):
    """Obligaciones del docente entre dos fechas, con su marcación si existe.

    Devuelve una lista de dicts con el formato que espera marcacion_service,
    más la clave "fecha".
    """
    hasta = hasta or desde
    clases = consultar(
        """
        SELECT dia::date AS fecha, h.id AS horario_catedra_id,
               c.nombre || ' (' || ca.nombre || ')' AS descripcion,
               h.hora_inicio AS inicio, h.hora_fin AS fin,
               a.id AS asistencia_id, a.entrada, a.salida,
               a.tardanza, a.salida_anticipada, a.motivo_correccion,
               (
                   SELECT CASE n.tipo WHEN 'feriado' THEN 'Feriado' ELSE 'Receso' END
                          || ': ' || n.descripcion
                   FROM dia_no_laborable n
                   WHERE dia::date BETWEEN n.fecha_desde AND n.fecha_hasta
                   ORDER BY n.tipo, n.id
                   LIMIT 1
               ) AS no_laborable
        FROM generate_series(%s::date, %s::date, interval '1 day') AS dia
        JOIN horario_catedra h
            ON h.dia_semana = EXTRACT(ISODOW FROM dia)
           AND h.vigente_desde <= dia::date
           AND (h.vigente_hasta IS NULL OR h.vigente_hasta >= dia::date)
        JOIN catedra c ON c.id = h.catedra_id
        JOIN carrera ca ON ca.id = c.carrera_id
        LEFT JOIN asistencia a
            ON a.horario_catedra_id = h.id AND a.fecha = dia::date
        WHERE h.docente_id = %s;
        """,
        (desde, hasta, docente_id),
    )
    actividades = consultar(
        """
        SELECT ae.fecha, ad.id AS actividad_docente_id,
               ae.tipo::text AS tipo_actividad, ae.descripcion AS detalle,
               ad.rol::text AS rol,
               ae.hora_inicio AS inicio, ae.hora_fin AS fin,
               a.id AS asistencia_id, a.entrada, a.salida,
               a.tardanza, a.salida_anticipada, a.motivo_correccion
        FROM actividad_docente ad
        JOIN actividad_especial ae ON ae.id = ad.actividad_id
        LEFT JOIN asistencia a ON a.actividad_docente_id = ad.id AND a.fecha = ae.fecha
        WHERE ad.docente_id = %s AND ae.fecha BETWEEN %s AND %s;
        """,
        (docente_id, desde, hasta),
    )

    obligaciones = []
    for fila in clases:
        obligaciones.append(dict(fila, tipo="clase", actividad_docente_id=None))
    for fila in actividades:
        descripcion = f"{TIPOS_ACTIVIDAD[fila['tipo_actividad']]}: {fila['detalle']}"
        if fila["rol"]:
            descripcion += f" - {ROLES[fila['rol']]}"
        obligaciones.append(
            dict(
                fila, tipo="actividad", horario_catedra_id=None,
                descripcion=descripcion, no_laborable=None,
            )
        )
    obligaciones.sort(key=lambda o: (o["fecha"], o["inicio"], o["fin"]))
    return obligaciones


def registrar_entradas(docente_id, fecha, items, momento):
    """Inserta la entrada de cada obligación del bloque en una sola transacción."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                cur.execute(
                    """
                    INSERT INTO asistencia
                        (docente_id, fecha, horario_catedra_id, actividad_docente_id,
                         inicio_previsto, fin_previsto, entrada, tardanza)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        docente_id,
                        fecha,
                        item["horario_catedra_id"],
                        item["actividad_docente_id"],
                        item["inicio"],
                        item["fin"],
                        momento,
                        item["tardanza"],
                    ),
                )
        conn.commit()


def registrar_salidas(items, momento):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for item in items:
                cur.execute(
                    """
                    UPDATE asistencia
                    SET salida = %s, salida_anticipada = %s
                    WHERE id = %s AND salida IS NULL;
                    """,
                    (momento, item["salida_anticipada"], item["asistencia_id"]),
                )
        conn.commit()


def corregir_marcacion(docente_id, fila, correccion, motivo, usuario_id, momento):
    """Carga o corrige a mano la marcación de una obligación y deja quién lo hizo.

    fila: obligación ya clasificada (situacion_service.clasificar).
    correccion: salida de marcacion_service.preparar_correccion.
    """
    datos = (
        correccion["entrada"], correccion["salida"], correccion["tardanza"],
        correccion["salida_anticipada"], usuario_id, momento, motivo,
    )
    if fila["asistencia_id"]:
        ejecutar(
            """
            UPDATE asistencia
            SET entrada = %s, salida = %s, tardanza = %s, salida_anticipada = %s,
                corregida_por = %s, corregida_el = %s, motivo_correccion = %s
            WHERE id = %s;
            """,
            datos + (fila["asistencia_id"],),
        )
    else:
        ejecutar(
            """
            INSERT INTO asistencia
                (entrada, salida, tardanza, salida_anticipada,
                 corregida_por, corregida_el, motivo_correccion,
                 docente_id, fecha, horario_catedra_id, actividad_docente_id,
                 inicio_previsto, fin_previsto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            datos + (
                docente_id, fila["fecha"], fila["horario_catedra_id"],
                fila["actividad_docente_id"], fila["inicio"], fila["fin"],
            ),
        )
