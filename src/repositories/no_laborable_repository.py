"""Feriados y recesos: días en los que las clases habituales no se dictan."""

from config.database import consultar, ejecutar


def listar():
    return consultar(
        """
        SELECT n.id, n.tipo::text AS tipo, n.descripcion, n.fecha_desde, n.fecha_hasta,
               u.nombre_usuario
        FROM dia_no_laborable n
        JOIN usuario u ON u.id = n.usuario_id
        ORDER BY n.fecha_desde DESC, n.id DESC;
        """
    )


def del_dia(fecha):
    """Feriados y recesos que abarcan esa fecha, como textos "Feriado: ..."."""
    filas = consultar(
        """
        SELECT CASE tipo WHEN 'feriado' THEN 'Feriado' ELSE 'Receso' END
               || ': ' || descripcion AS texto
        FROM dia_no_laborable
        WHERE %s BETWEEN fecha_desde AND fecha_hasta
        ORDER BY tipo, id;
        """,
        (fecha,),
    )
    return [fila["texto"] for fila in filas]


def registrar(tipo, descripcion, desde, hasta, usuario_id):
    ejecutar(
        """
        INSERT INTO dia_no_laborable (tipo, descripcion, fecha_desde, fecha_hasta, usuario_id)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (tipo, descripcion, desde, hasta, usuario_id),
    )


def eliminar(no_laborable_id):
    ejecutar("DELETE FROM dia_no_laborable WHERE id = %s;", (no_laborable_id,))
