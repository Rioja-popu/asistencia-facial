import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services import usuario_service as u


def usuario(id=1, nombre="admin", contrasenia="secreta1", activo=True, **otros):
    return {
        "id": id, "nombre_usuario": nombre, "contrasenia": u.cifrar(contrasenia),
        "activo": activo, "correo_electronico": None, "dni": None, "cuil": None, **otros,
    }


def alta(nombre="preceptor", rol=u.ADMINISTRATIVO, contrasenia="secreta1", repetida=None, **otros):
    return u.preparar_alta(
        nombre, rol, contrasenia, contrasenia if repetida is None else repetida, **otros
    )


# ------------------------------------------------------------------ contraseñas
def test_la_contrasenia_no_se_guarda_en_texto_plano():
    guardada = u.cifrar("secreta1")
    assert "secreta1" not in guardada
    assert u.esta_cifrada(guardada)
    assert u.coincide("secreta1", guardada)
    assert not u.coincide("Secreta1", guardada)


def test_dos_usuarios_con_la_misma_contrasenia_guardan_valores_distintos():
    assert u.cifrar("secreta1") != u.cifrar("secreta1")


def test_el_admin_inicial_ingresa_con_admin():
    ruta = os.path.join(os.path.dirname(__file__), "..", "database", "initdb",
                        "02-datos-iniciales.sql")
    with open(ruta, encoding="utf-8") as archivo:
        guardada = archivo.read().split("'")[-2]
    assert u.esta_cifrada(guardada) and u.coincide("admin", guardada)


def test_una_contrasenia_anterior_en_texto_plano_sigue_sirviendo():
    assert not u.esta_cifrada("admin")
    assert u.coincide("admin", "admin")
    assert not u.coincide("otra", "admin")


def test_un_valor_guardado_roto_no_deja_ingresar():
    assert not u.coincide("x", "pbkdf2_sha256$roto")


def test_no_se_puede_ingresar_tipeando_el_hash():
    guardada = u.cifrar("secreta1")
    assert not u.coincide(guardada, guardada)


def test_contrasenia_corta_o_mal_repetida():
    with pytest.raises(ValueError, match="al menos 6"):
        u.validar_contrasenia("12345", "12345")
    with pytest.raises(ValueError, match="no coinciden"):
        u.validar_contrasenia("secreta1", "secreta2")
    u.validar_contrasenia("123456", "123456")


# ----------------------------------------------------------------------- ingreso
def test_autenticar_devuelve_el_usuario_con_esa_contrasenia():
    candidatos = [usuario(1, contrasenia="unaclave"), usuario(2, contrasenia="otraclave")]
    assert u.autenticar(candidatos, "otraclave")["id"] == 2
    assert u.autenticar(candidatos, "ninguna") is None
    assert u.autenticar([], "unaclave") is None


def test_un_usuario_inactivo_no_ingresa():
    assert u.autenticar([usuario(activo=False)], "secreta1") is None


# ------------------------------------------------------------------------- altas
def test_alta_valida_guarda_la_contrasenia_cifrada_y_normaliza():
    datos = alta(" preceptor ", correo=" pre@ies7.edu.ar ", dni="30.111.222", cuil="27-30111222-4")
    assert datos["nombre_usuario"] == "preceptor"
    assert datos["rol"] == u.ADMINISTRATIVO
    assert u.coincide("secreta1", datos["contrasenia"])
    assert (datos["correo_electronico"], datos["dni"], datos["cuil"]) == (
        "pre@ies7.edu.ar", "30111222", "27301112224"
    )


def test_alta_sin_datos_opcionales():
    datos = alta()
    assert (datos["correo_electronico"], datos["dni"], datos["cuil"]) == (None, None, None)


@pytest.mark.parametrize(
    "cambios, mensaje",
    [
        ({"nombre": "ab"}, "al menos 3"),
        ({"nombre": "dos palabras"}, "sin espacios"),
        ({"rol": "director"}, "rol"),
        ({"contrasenia": "123"}, "al menos 6"),
        ({"repetida": "distinta1"}, "no coinciden"),
        ({"correo": "sin-arroba"}, "correo"),
        ({"dni": "123"}, "DNI"),
        ({"cuil": "20-123-4"}, "CUIL"),
    ],
)
def test_alta_invalida(cambios, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        alta(**cambios)


def test_no_se_repite_el_nombre_de_usuario_ni_con_otras_mayusculas():
    with pytest.raises(ValueError, match="ese nombre"):
        u.validar_sin_repetidos(alta("ADMIN"), [usuario(nombre="admin")])


def test_no_se_repite_nada_que_sirva_para_ingresar():
    existente = usuario(nombre="admin", dni="30111222")
    with pytest.raises(ValueError, match="correo, DNI o CUIL"):
        u.validar_sin_repetidos(alta(dni="30111222"), [existente])
    u.validar_sin_repetidos(alta(dni="30111223"), [existente])


# ------------------------------------------------------------------------- bajas
def test_no_se_puede_eliminar_al_usuario_conectado():
    with pytest.raises(ValueError, match="conectado"):
        u.validar_baja(usuario(id=1), 1)
    u.validar_baja(usuario(id=2), 1)
