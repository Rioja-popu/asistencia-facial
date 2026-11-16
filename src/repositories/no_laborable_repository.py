"""Feriados y recesos: días en los que las clases habituales no se dictan."""

from config.database import consultar, ejecutar


def listar():
    return consultar(
        """
        SELECT id, tipo::text AS tipo, descripcion, fecha_desde, fecha_hasta
        FROM dia_no_laborable
        ORDER BY fecha_desde DESC, id DESC;
        """
    )


def registrar(tipo, descripcion, desde, hasta):
    ejecutar(
        """
        INSERT INTO dia_no_laborable (tipo, descripcion, fecha_desde, fecha_hasta)
        VALUES (%s, %s, %s, %s);
        """,
        (tipo, descripcion, desde, hasta),
    )


def eliminar(no_laborable_id):
    ejecutar("DELETE FROM dia_no_laborable WHERE id = %s;", (no_laborable_id,))
