import psycopg
from config.database import get_connection
from datetime import datetime, time, timedelta

# Supongamos que usas tu función de conexión get_db_connection()


def crear_jornada(fecha, horario_entrada, horario_salida, catedra, usuario_id):
    query = """
        INSERT INTO jornada (fecha, horario_entrada, horario_salida, catedra, usuario_id)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (fecha, horario_entrada, horario_salida, catedra, usuario_id),
            )
            jornada_id = cur.fetchone()[0]
            conn.commit()
            return jornada_id


def actualizar_jornada(
    jornada_id, fecha, horario_entrada, horario_salida, catedra
):
    """Actualiza los datos de una jornada existente manteniendo el mismo jornada_id."""
    query = """
        UPDATE jornada
        SET fecha = %s, horario_entrada = %s, horario_salida = %s, catedra = %s
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                query,
                (fecha, horario_entrada, horario_salida, catedra, jornada_id),
            )
            conn.commit()


def obtener_asistencia_alumno(jornada_id, alumno_id):
    """Obtiene el registro de asistencia del alumno para una jornada específica si existe."""
    query = """
        SELECT id, entrada, salida
        FROM asistencia
        WHERE jornada_id = %s AND alumno_id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (jornada_id, alumno_id))
            return cur.fetchone()  # Retorna (id, horario_entrada, horario_salida) o None


def registrar_entrada_asistencia(jornada_id, alumno_id, ahora=None):
    if ahora is None:
        from datetime import datetime

        ahora = datetime.now()

    query = """
        INSERT INTO asistencia (jornada_id, alumno_id, entrada)
        VALUES (%s, %s, %s);
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (jornada_id, alumno_id, ahora))
            conn.commit()


def registrar_salida_asistencia(asistencia_id, ahora=None):
    if ahora is None:
        from datetime import datetime

        ahora = datetime.now()

    query = """
        UPDATE asistencia
        SET salida = %s
        WHERE id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (ahora, asistencia_id))
            conn.commit()


def obtener_alumnos_con_fotos():
    """
    Recupera cada alumno con sus 3 fotos (frontal, lateral_izquierdo, lateral_derecho)
    haciendo LEFT JOIN individual para cada tipo de ángulo.
    Retorna: [(id, nombre, apellido, bytes_frontal, bytes_izq, bytes_der), ...]
    """
    query = """
        SELECT 
            a.id,
            a.nombre,
            a.apellido,
            f_front.imagen AS frontal,
            f_izq.imagen AS lateral_izquierdo,
            f_der.imagen AS lateral_derecho
        FROM alumno a
        LEFT JOIN foto_alumno f_front 
            ON a.id = f_front.alumno_id AND f_front.angulo = 'frontal'
        LEFT JOIN foto_alumno f_izq 
            ON a.id = f_izq.alumno_id AND f_izq.angulo = 'lateral_izquierdo'
        LEFT JOIN foto_alumno f_der 
            ON a.id = f_der.alumno_id AND f_der.angulo = 'lateral_derecho';
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def obtener_jornadas_usuario(usuario_id):
    """
    Jornadas registradas por el usuario, de la más reciente a la más antigua.
    Retorna: [(id, fecha, catedra, horario_entrada, horario_salida), ...]
    """
    query = """
        SELECT id, fecha, catedra, horario_entrada, horario_salida
        FROM jornada
        WHERE usuario_id = %s
        ORDER BY fecha DESC, horario_entrada DESC, id DESC;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (usuario_id,))
            return cur.fetchall()


def obtener_jornada_de_usuario(jornada_id, usuario_id):
    """Datos de la Jornada para el informe, o None si no pertenece al usuario."""
    query = """
        SELECT j.id, j.fecha, j.catedra, j.horario_entrada, j.horario_salida,
               u.nombre_usuario
        FROM jornada j
        JOIN usuario u ON u.id = j.usuario_id
        WHERE j.id = %s AND j.usuario_id = %s;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (jornada_id, usuario_id))
            fila = cur.fetchone()
    if fila is None:
        return None
    claves = (
        "id",
        "fecha",
        "catedra",
        "horario_entrada",
        "horario_salida",
        "nombre_usuario",
    )
    return dict(zip(claves, fila))


def obtener_asistencias_jornada(jornada_id, usuario_id):
    """
    Alumnos con asistencia en la Jornada, sólo si la Jornada pertenece al usuario.
    Retorna: [(apellido, nombre, dni, libreta, entrada, salida), ...]
    """
    query = """
        SELECT al.apellido, al.nombre, al.dni, al.libreta, a.entrada, a.salida
        FROM asistencia a
        JOIN jornada j ON j.id = a.jornada_id
        JOIN alumno al ON al.id = a.alumno_id
        WHERE j.id = %s AND j.usuario_id = %s
        ORDER BY LOWER(al.apellido), LOWER(al.nombre), al.id;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (jornada_id, usuario_id))
            return cur.fetchall()
