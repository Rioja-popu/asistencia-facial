"""Guarda en una sola transacción lo que arma importacion_service.planificar."""

from config.database import consultar, get_connection


def listar_horarios_vigentes(desde):
    return consultar(
        """
        SELECT docente_id, catedra_id, dia_semana, hora_inicio, hora_fin
        FROM horario_catedra
        WHERE vigente_hasta IS NULL OR vigente_hasta >= %s;
        """,
        (desde,),
    )


def importar(horarios, desde):
    """Crea las carreras, cátedras y docentes que falten y todos los horarios.

    Los docentes nuevos quedan sin DNI, CUIL ni fotos: se completan en Docentes.
    Si algo falla no se guarda nada.
    """
    carreras, catedras, docentes = {}, {}, {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            for h in horarios:
                clave_carrera, clave_catedra, clave_docente = h["claves"]
                carrera_id = h["carrera_id"] or carreras.get(clave_carrera)
                if carrera_id is None:
                    cur.execute(
                        "INSERT INTO carrera (nombre) VALUES (%s) RETURNING id;",
                        (h["carrera"],),
                    )
                    carrera_id = carreras[clave_carrera] = cur.fetchone()[0]
                catedra_id = h["catedra_id"] or catedras.get(clave_catedra)
                if catedra_id is None:
                    cur.execute(
                        """
                        INSERT INTO catedra (carrera_id, nombre, anio)
                        VALUES (%s, %s, %s) RETURNING id;
                        """,
                        (carrera_id, h["catedra"], h["anio"]),
                    )
                    catedra_id = catedras[clave_catedra] = cur.fetchone()[0]
                docente_id = h["docente_id"] or docentes.get(clave_docente)
                if docente_id is None:
                    cur.execute(
                        "INSERT INTO docente (apellido, nombre) VALUES (%s, %s) RETURNING id;",
                        (h["apellido"], h["nombre"]),
                    )
                    docente_id = docentes[clave_docente] = cur.fetchone()[0]
                cur.execute(
                    """
                    INSERT INTO horario_catedra
                        (docente_id, catedra_id, dia_semana, hora_inicio, hora_fin, vigente_desde)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (docente_id, catedra_id, h["dia"], h["inicio"], h["fin"], desde),
                )
        conn.commit()
