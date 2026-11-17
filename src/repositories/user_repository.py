"""Usuarios del sistema (personal administrativo que opera la aplicación)."""

from config.database import consultar, ejecutar

_CAMPOS = "id, nombre_usuario, correo_electronico, dni, cuil, rol, activo"


def buscar_para_ingreso(identificador):
    """Usuarios que coinciden con lo tipeado en el login, con su contraseña guardada."""
    return consultar(
        f"""
        SELECT {_CAMPOS}, contrasenia
        FROM usuario
        WHERE LOWER(nombre_usuario) = LOWER(%s)
           OR LOWER(correo_electronico) = LOWER(%s)
           OR dni = %s
           OR cuil = %s
        ORDER BY id;
        """,
        (identificador,) * 4,
    )


def obtener(usuario_id):
    filas = consultar(f"SELECT {_CAMPOS}, contrasenia FROM usuario WHERE id = %s;", (usuario_id,))
    return filas[0] if filas else None


def listar():
    """Todos los usuarios; `con_historial` indica si hay registros cargados a su nombre."""
    return consultar(
        f"""
        SELECT {_CAMPOS},
               EXISTS (SELECT 1 FROM ausencia a WHERE a.usuario_id = u.id)
               OR EXISTS (SELECT 1 FROM asistencia s WHERE s.corregida_por = u.id)
               OR EXISTS (SELECT 1 FROM dia_no_laborable n WHERE n.usuario_id = u.id)
               AS con_historial
        FROM usuario u
        ORDER BY activo DESC, LOWER(nombre_usuario);
        """
    )


def crear(datos):
    ejecutar(
        """
        INSERT INTO usuario (nombre_usuario, rol, contrasenia, correo_electronico, dni, cuil)
        VALUES (%(nombre_usuario)s, %(rol)s, %(contrasenia)s, %(correo_electronico)s,
                %(dni)s, %(cuil)s);
        """,
        datos,
    )


def guardar_contrasenia(usuario_id, contrasenia_cifrada):
    ejecutar(
        "UPDATE usuario SET contrasenia = %s WHERE id = %s;", (contrasenia_cifrada, usuario_id)
    )


def cambiar_activo(usuario_id, activo):
    ejecutar("UPDATE usuario SET activo = %s WHERE id = %s;", (activo, usuario_id))


def eliminar(usuario_id):
    ejecutar("DELETE FROM usuario WHERE id = %s;", (usuario_id,))
