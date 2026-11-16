from config.database import consultar, get_connection


def listar_docentes(solo_activos=False):
    filtro = "WHERE activo" if solo_activos else ""
    return consultar(
        f"""
        SELECT id, apellido, nombre, dni, cuil, celular, correo_electronico, activo
        FROM docente
        {filtro}
        ORDER BY LOWER(apellido), LOWER(nombre), id;
        """
    )


def guardar_docente(datos, fotos, docente_id=None):
    """Crea o actualiza un docente y sus fotos en una misma transacción.

    datos = (apellido, nombre, dni, cuil, celular, correo_electronico, activo)
    fotos = {angulo: bytes}; al editar sólo se reemplazan los ángulos recibidos.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if docente_id is None:
                cur.execute(
                    """
                    INSERT INTO docente
                        (apellido, nombre, dni, cuil, celular, correo_electronico, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    datos,
                )
                docente_id = cur.fetchone()[0]
            else:
                cur.execute(
                    """
                    UPDATE docente
                    SET apellido = %s, nombre = %s, dni = %s, cuil = %s,
                        celular = %s, correo_electronico = %s, activo = %s
                    WHERE id = %s;
                    """,
                    (*datos, docente_id),
                )
            for angulo, imagen in fotos.items():
                cur.execute(
                    """
                    INSERT INTO foto_docente (docente_id, angulo, imagen)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (docente_id, angulo)
                    DO UPDATE SET imagen = EXCLUDED.imagen;
                    """,
                    (docente_id, angulo, imagen),
                )
        conn.commit()
    return docente_id


def obtener_fotos(docente_id):
    filas = consultar(
        "SELECT angulo::text AS angulo, imagen FROM foto_docente WHERE docente_id = %s;",
        (docente_id,),
    )
    return {fila["angulo"]: bytes(fila["imagen"]) for fila in filas}


def obtener_docentes_con_fotos():
    """Docentes activos con sus fotos, para generar las referencias faciales.

    Devuelve [(id, nombre, apellido, frontal, lateral_izquierdo, lateral_derecho), ...]
    """
    filas = consultar(
        """
        SELECT
            d.id, d.nombre, d.apellido,
            f_front.imagen AS frontal,
            f_izq.imagen AS lateral_izquierdo,
            f_der.imagen AS lateral_derecho
        FROM docente d
        LEFT JOIN foto_docente f_front
            ON d.id = f_front.docente_id AND f_front.angulo = 'frontal'
        LEFT JOIN foto_docente f_izq
            ON d.id = f_izq.docente_id AND f_izq.angulo = 'lateral_izquierdo'
        LEFT JOIN foto_docente f_der
            ON d.id = f_der.docente_id AND f_der.angulo = 'lateral_derecho'
        WHERE d.activo;
        """
    )
    return [
        (
            f["id"], f["nombre"], f["apellido"],
            f["frontal"], f["lateral_izquierdo"], f["lateral_derecho"],
        )
        for f in filas
    ]


def docente_esta_activo(docente_id):
    filas = consultar("SELECT activo FROM docente WHERE id = %s;", (docente_id,))
    return bool(filas) and filas[0]["activo"]
