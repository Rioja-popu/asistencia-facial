"""Reglas de los usuarios del sistema: contraseñas cifradas, roles, altas y bajas."""

import hashlib
import hmac
import secrets

ADMINISTRADOR = "administrador"
ADMINISTRATIVO = "administrativo"
ROLES = {ADMINISTRADOR: "Administrador", ADMINISTRATIVO: "Administrativo"}

LARGO_MINIMO = 6
_ALGORITMO = "pbkdf2_sha256"
_VUELTAS = 200_000


def cifrar(contrasenia, sal=None):
    """Devuelve lo que se guarda en la base: nunca la contraseña, sino su hash con sal."""
    sal = sal or secrets.token_hex(16)
    resumen = hashlib.pbkdf2_hmac("sha256", contrasenia.encode(), bytes.fromhex(sal), _VUELTAS)
    return f"{_ALGORITMO}${_VUELTAS}${sal}${resumen.hex()}"


def esta_cifrada(guardada):
    return guardada.startswith(_ALGORITMO + "$")


def coincide(contrasenia, guardada):
    if not esta_cifrada(guardada):
        # Contraseña anterior a la migración, todavía en texto plano
        return hmac.compare_digest(contrasenia.encode(), guardada.encode())
    try:
        _, vueltas, sal, resumen = guardada.split("$")
        calculado = hashlib.pbkdf2_hmac(
            "sha256", contrasenia.encode(), bytes.fromhex(sal), int(vueltas)
        )
    except ValueError:
        return False
    return hmac.compare_digest(calculado.hex(), resumen)


def autenticar(candidatos, contrasenia):
    """El usuario activo, entre los que coinciden con lo tipeado, cuya contraseña es esa."""
    for usuario in candidatos:
        if usuario["activo"] and coincide(contrasenia, usuario["contrasenia"]):
            return usuario
    return None


def validar_contrasenia(nueva, repetida):
    if len(nueva) < LARGO_MINIMO:
        raise ValueError(f"La contraseña debe tener al menos {LARGO_MINIMO} caracteres.")
    if nueva != repetida:
        raise ValueError("Las dos contraseñas no coinciden.")


def _solo_numeros(valor, nombre, largos):
    numeros = valor.replace(".", "").replace("-", "").replace(" ", "")
    if not numeros:
        return None
    if not numeros.isdigit() or len(numeros) not in largos:
        cantidad = " u ".join(str(largo) for largo in largos)
        raise ValueError(f"El {nombre} debe tener {cantidad} números.")
    return numeros


def preparar_alta(nombre_usuario, rol, contrasenia, repetida, correo="", dni="", cuil=""):
    """Valida los datos de un usuario nuevo y devuelve lo que se guarda."""
    nombre_usuario = nombre_usuario.strip()
    if len(nombre_usuario) < 3 or " " in nombre_usuario:
        raise ValueError("El nombre de usuario debe tener al menos 3 caracteres, sin espacios.")
    if rol not in ROLES:
        raise ValueError("Elegí un rol.")
    validar_contrasenia(contrasenia, repetida)
    correo = correo.strip() or None
    if correo and ("@" not in correo or " " in correo):
        raise ValueError("El correo electrónico no es válido.")
    return {
        "nombre_usuario": nombre_usuario,
        "rol": rol,
        "contrasenia": cifrar(contrasenia),
        "correo_electronico": correo,
        "dni": _solo_numeros(dni, "DNI", (7, 8)),
        "cuil": _solo_numeros(cuil, "CUIL", (11,)),
    }


def identificadores(usuario):
    """Todo lo que sirve para ingresar: no puede repetirse entre usuarios."""
    campos = ("nombre_usuario", "correo_electronico", "dni", "cuil")
    return {usuario[campo].lower() for campo in campos if usuario.get(campo)}


def validar_sin_repetidos(nuevo, existentes):
    usados = set()
    for usuario in existentes:
        usados |= identificadores(usuario)
    repetidos = identificadores(nuevo) & usados
    if nuevo["nombre_usuario"].lower() in repetidos:
        raise ValueError("Ya existe un usuario con ese nombre.")
    if repetidos:
        raise ValueError("Ya hay un usuario con ese correo, DNI o CUIL.")


def validar_baja(usuario, usuario_actual_id):
    """Quién puede eliminarse o desactivarse. Siempre queda un administrador: el que opera."""
    if usuario["id"] == usuario_actual_id:
        raise ValueError("No podés eliminar ni desactivar el usuario con el que estás conectado.")
