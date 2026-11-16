import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services import importacion_docentes_service as imp


def fila(apellido="Maraz", nombre="Santiago Federico", dni="28456123", cuil="20284561234",
         celular="3885550101", correo="smaraz@example.com", numero=2):
    return {
        "fila": numero, "apellido": apellido, "nombre": nombre, "dni": dni, "cuil": cuil,
        "celular": celular, "correo_electronico": correo,
    }


def existente(id_=1, apellido="Maraz", nombre="Santiago Federico", dni=None, cuil=None,
              celular=None, correo=None):
    return {
        "id": id_, "apellido": apellido, "nombre": nombre, "dni": dni, "cuil": cuil,
        "celular": celular, "correo_electronico": correo, "activo": True,
    }


def test_planilla_modelo_se_lee_con_dni_y_cuil_como_texto(tmp_path):
    ruta = str(tmp_path / "docentes.xlsx")
    imp.generar_planilla(ruta, [
        ("MARAZ", "SANTIAGO FEDERICO", "28.456.123", "20-28456123-4", "388 555-0101",
         "smaraz@example.com"),
    ])
    docentes, errores = imp.leer_listado(ruta)
    assert errores == []
    assert docentes == [fila()]


def test_lee_csv_con_punto_y_coma_y_encabezados_alternativos(tmp_path):
    ruta = tmp_path / "docentes.csv"
    ruta.write_text(
        "Listado de docentes;;;\nApellidos;Nombres;Documento;E-mail\n"
        "Núñez;María José;7123456;mnunez@example.com\n;;;\n",
        encoding="latin-1",
    )
    docentes, errores = imp.leer_listado(str(ruta))
    assert errores == []
    assert docentes == [fila("Núñez", "María José", "7123456", "", "", "mnunez@example.com", 3)]


def test_sin_encabezado_no_lee_nada(tmp_path):
    ruta = tmp_path / "docentes.csv"
    ruta.write_text("Maraz,Santiago,28456123\n", encoding="utf-8")
    docentes, errores = imp.leer_listado(str(ruta))
    assert docentes == [] and "APELLIDO" in errores[0]


def test_docente_nuevo_se_crea():
    plan = imp.planificar([fila()], [])
    assert [d["dni"] for d in plan["nuevos"]] == ["28456123"]
    assert plan["nuevos"][0]["aviso"] is None


def test_docente_importado_con_los_horarios_se_completa_y_no_se_duplica():
    plan = imp.planificar([fila("MARAZ", "santiago  federico")], [existente()])
    assert plan["nuevos"] == []
    (_, docente_id, faltantes), = plan["completados"]
    assert docente_id == 1
    assert faltantes == {
        "dni": "28456123", "cuil": "20284561234", "celular": "3885550101",
        "correo_electronico": "smaraz@example.com",
    }


def test_mismo_dni_no_se_duplica_ni_pisa_datos_cargados():
    cargado = existente(dni="28456123", cuil="20284561234", celular="3884000000")
    plan = imp.planificar([fila(nombre="Santiago")], [cargado])
    (_, _, faltantes), = plan["completados"]
    assert faltantes == {"correo_electronico": "smaraz@example.com"}
    completo = dict(cargado, correo_electronico="otro@example.com")
    assert len(imp.planificar([fila()], [completo])["sin_cambios"]) == 1


def test_mismo_nombre_con_otro_dni_es_error():
    plan = imp.planificar([fila()], [existente(dni="30111222")])
    assert plan["nuevos"] == [] and "otro DNI" in plan["errores"][0][1]


def test_nombre_parecido_se_crea_con_aviso():
    plan = imp.planificar([fila()], [existente(nombre="Santiago")])
    assert "se parece a Maraz, Santiago" in plan["nuevos"][0]["aviso"]


def test_errores_de_datos_y_repetidos():
    filas = [
        fila(numero=2),
        fila("Otro", "Docente", numero=3),                           # DNI repetido
        fila("Sin", "Dni", dni="", numero=4),
        fila("Dni", "Corto", dni="123", numero=5),
        fila("Cuil", "Malo", dni="30111222", cuil="20-1", numero=6),
        fila("Correo", "Malo", dni="30111223", cuil="", correo="sin arroba", numero=7),
        fila("", "Sin Apellido", dni="30111224", cuil="", numero=8),
        fila("Cuil", "Ajeno", dni="30111225", cuil="27999999990", numero=9),
    ]
    plan = imp.planificar(filas, [existente(9, "Gómez", "Ana", "11222333", "27999999990")])
    assert [d["fila"] for d in plan["nuevos"]] == [2]
    assert {d["fila"]: motivo for d, motivo in plan["errores"]} == {
        3: "el DNI está repetido en el listado",
        4: "falta el DNI",
        5: "el DNI tiene que tener 7 u 8 números",
        6: "el CUIL tiene que tener 11 números",
        7: "el correo electrónico no es válido",
        8: "falta el apellido o el nombre",
        9: "el CUIL ya pertenece a otro docente",
    }
