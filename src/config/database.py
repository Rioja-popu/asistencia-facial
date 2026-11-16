import os
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

def get_connection():
    return psycopg.connect(
        host="localhost",
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )


def consultar(query, params=()):
    """Ejecuta un SELECT y devuelve una lista de dicts."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def ejecutar(query, params=()):
    """Ejecuta un INSERT/UPDATE/DELETE. Devuelve la fila de RETURNING, si hay."""
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            fila = cur.fetchone() if cur.description else None
        conn.commit()
        return fila
