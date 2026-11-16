import os
import sys
from datetime import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openpyxl import load_workbook

from services import importacion_service as servicio

MARAZ = "MARAZ, SANTIAGO FEDERICO"
# Cuadro de 3ro de Ciencia de Datos: módulo -> [lunes, martes, miércoles, jueves, viernes]
CUADRO = [
    [f"ANALÍTICA WEB - {MARAZ}", f"RECONOCIMIENTO VISUAL - {MARAZ}",
     f"ANALÍTICA WEB - {MARAZ}", "", ""],
    [f"ANALÍTICA WEB - {MARAZ}", f"RECONOCIMIENTO VISUAL - {MARAZ}",
     f"ANALÍTICA WEB - {MARAZ}", "", ""],
    ["ÉTICA Y DEONTOLOGÍA PROFESIONAL - VILLARUBIA GOMEZ, EZEQUIEL", "", "",
     f"RECONOCIMIENTO VISUAL - {MARAZ}", ""],
    ["ÉTICA Y DEONTOLOGÍA PROFESIONAL - VILLARUBIA GOMEZ, EZEQUIEL", "", "",
     f"RECONOCIMIENTO VISUAL - {MARAZ}", ""],
    ["ÉTICA Y DEONTOLOGÍA PROFESIONAL - VILLARUBIA GOMEZ, EZEQUIEL", "", "", "", ""],
]


def planilla(tmp_path, cuadro=CUADRO, carrera="CIENCIA DE DATOS E INTELIGENCIA ARTIFICIAL",
             curso="3ro"):
    ruta = str(tmp_path / "horarios.xlsx")
    servicio.generar_planilla(ruta)
    libro = load_workbook(ruta)
    hoja = libro["Curso"]
    hoja["B3"] = carrera
    hoja["E3"] = curso
    for i, fila in enumerate(cuadro):
        for j, texto in enumerate(fila):
            hoja.cell(row=7 + i, column=2 + j, value=texto or None)
    libro.save(ruta)
    return ruta


def resumen(bloques):
    return {
        (b["dia"], b["inicio"], b["fin"], b["catedra"], b["apellido"]) for b in bloques
    }


def test_la_planilla_modelo_vacia_no_trae_horarios(tmp_path):
    ruta = str(tmp_path / "modelo.xlsx")
    servicio.generar_planilla(ruta)
    bloques, errores = servicio.leer_planilla(ruta)
    assert bloques == []
    assert errores == ['Hoja "Curso": falta el nombre de la carrera.',
                       'Hoja "Curso": falta el curso (1ro a 6to).']


def test_une_los_modulos_seguidos_de_la_misma_catedra_y_docente(tmp_path):
    bloques, errores = servicio.leer_planilla(planilla(tmp_path))
    assert errores == []
    assert resumen(bloques) == {
        (1, time(8, 0), time(9, 20), "ANALÍTICA WEB", "Maraz"),
        (1, time(9, 20), time(11, 20), "ÉTICA Y DEONTOLOGÍA PROFESIONAL", "Villarubia Gomez"),
        (2, time(8, 0), time(9, 20), "RECONOCIMIENTO VISUAL", "Maraz"),
        (3, time(8, 0), time(9, 20), "ANALÍTICA WEB", "Maraz"),
        (4, time(9, 20), time(10, 40), "RECONOCIMIENTO VISUAL", "Maraz"),
    }
    assert {(b["carrera"], b["anio"], b["nombre"]) for b in bloques if b["dia"] == 2} == {
        ("CIENCIA DE DATOS E INTELIGENCIA ARTIFICIAL", 3, "Santiago Federico")
    }


def test_celda_sin_el_formato_se_informa_y_no_se_importa(tmp_path):
    cuadro = [["ANALÍTICA WEB MARAZ", "", "", "", ""]]
    bloques, errores = servicio.leer_planilla(planilla(tmp_path, cuadro))
    assert bloques == []
    assert len(errores) == 1 and "MATERIA - APELLIDO, NOMBRE" in errores[0]


def test_materia_con_guion_en_el_nombre(tmp_path):
    cuadro = [["TALLER - NIVEL I - PEREZ, ANA", "", "", "", ""]] * 2
    bloques, _ = servicio.leer_planilla(planilla(tmp_path, cuadro))
    assert [(b["catedra"], b["apellido"], b["nombre"]) for b in bloques] == [
        ("TALLER - NIVEL I", "Perez", "Ana")
    ]


def test_plan_en_base_vacia_crea_todo_una_sola_vez(tmp_path):
    bloques, _ = servicio.leer_planilla(planilla(tmp_path))
    plan = servicio.planificar(bloques, [], [], [], [])
    assert len(plan["horarios"]) == 5 and not plan["errores"] and not plan["omitidos"]
    assert plan["carreras_nuevas"] == ["CIENCIA DE DATOS E INTELIGENCIA ARTIFICIAL"]
    assert len(plan["catedras_nuevas"]) == 3
    assert sorted(plan["docentes_nuevos"]) == [
        "Maraz, Santiago Federico", "Villarubia Gomez, Ezequiel"
    ]


def test_plan_reutiliza_lo_existente_sin_importar_tildes_ni_mayusculas(tmp_path):
    bloques, _ = servicio.leer_planilla(planilla(tmp_path))
    carrera = "Ciencia de Datos e Inteligencia Artificial"
    plan = servicio.planificar(
        bloques,
        [{"id": 1, "nombre": carrera}],
        [{"id": 10, "nombre": "Analitica Web", "anio": 3, "carrera": carrera}],
        [{"id": 7, "apellido": "maraz", "nombre": "Santiago Federico"}],
        [{"docente_id": 7, "catedra_id": 10, "dia_semana": 1,
          "hora_inicio": time(8, 0), "hora_fin": time(9, 20)}],
    )
    assert plan["carreras_nuevas"] == []
    assert plan["docentes_nuevos"] == ["Villarubia Gomez, Ezequiel"]
    assert len(plan["catedras_nuevas"]) == 2
    assert [(b["dia"], b["catedra"]) for b in plan["omitidos"]] == [(1, "ANALÍTICA WEB")]
    del_miercoles = next(h for h in plan["horarios"] if h["dia"] == 3)
    assert (del_miercoles["carrera_id"], del_miercoles["catedra_id"],
            del_miercoles["docente_id"]) == (1, 10, 7)


def test_plan_rechaza_superposicion_con_un_horario_ya_cargado(tmp_path):
    bloques, _ = servicio.leer_planilla(planilla(tmp_path))
    plan = servicio.planificar(
        bloques, [], [{"id": 99, "nombre": "Estadística", "anio": 2, "carrera": "Otra"}],
        [{"id": 7, "apellido": "Maraz", "nombre": "Santiago Federico"}],
        [{"docente_id": 7, "catedra_id": 99, "dia_semana": 2,
          "hora_inicio": time(8, 40), "hora_fin": time(10, 0)}],
    )
    assert len(plan["horarios"]) == 4
    (bloque, motivo), = plan["errores"]
    assert bloque["dia"] == 2 and "Estadística" in motivo


def test_plan_rechaza_un_modulo_suelto_de_40_minutos(tmp_path):
    cuadro = [["TALLER - PEREZ, ANA", "", "", "", ""]]
    bloques, _ = servicio.leer_planilla(planilla(tmp_path, cuadro))
    plan = servicio.planificar(bloques, [], [], [], [])
    assert plan["horarios"] == [] and "40 minutos" in plan["errores"][0][1]
    assert plan["carreras_nuevas"] == plan["docentes_nuevos"] == []


def test_duracion_valida_en_modulos_de_40_desde_una_clase():
    assert [m for m in (40, 80, 100, 120, 160) if servicio.duracion_valida(m)] == [80, 120, 160]
