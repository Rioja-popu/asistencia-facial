import os
import sys
from datetime import datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services.marcacion_service import (
    ENTRADA,
    SALIDA,
    es_salida_anticipada,
    es_tardanza,
    proponer_marcacion,
    separar_reemplazadas,
)

HOY = (2026, 11, 16)


def momento(hora, minuto, segundo=0):
    return datetime(*HOY, hora, minuto, segundo)


def clase(inicio, fin, descripcion="Programación I", entrada=None, salida=None, id_=1):
    return {
        "tipo": "clase",
        "horario_catedra_id": id_,
        "actividad_docente_id": None,
        "descripcion": descripcion,
        "inicio": time(*inicio),
        "fin": time(*fin),
        "asistencia_id": id_ if entrada else None,
        "entrada": entrada,
        "salida": salida,
    }


def actividad(inicio, fin, descripcion="Mesa de examen", id_=50):
    o = clase(inicio, fin, descripcion, id_=id_)
    o.update(tipo="actividad", horario_catedra_id=None, actividad_docente_id=id_)
    return o


def test_tardanza_solo_pasados_los_cinco_minutos():
    assert not es_tardanza(momento(8, 5, 59), time(8, 0))
    assert es_tardanza(momento(8, 6), time(8, 0))
    assert not es_tardanza(momento(7, 40), time(8, 0))


def test_salida_anticipada():
    assert es_salida_anticipada(momento(9, 19), time(9, 20))
    assert not es_salida_anticipada(momento(9, 20, 30), time(9, 20))


def test_sin_obligaciones_no_propone_nada():
    propuesta = proponer_marcacion([], momento(8, 0))
    assert propuesta["operacion"] is None
    assert "No tenés actividad programada" in propuesta["motivo"]


def test_entrada_en_horario():
    propuesta = proponer_marcacion([clase((8, 0), (9, 20))], momento(7, 50))
    assert propuesta["operacion"] == ENTRADA
    assert propuesta["items"][0]["tardanza"] is False


def test_entrada_con_tardanza():
    propuesta = proponer_marcacion([clase((8, 0), (9, 20))], momento(8, 10))
    assert propuesta["operacion"] == ENTRADA
    assert propuesta["items"][0]["tardanza"] is True


def test_demasiado_temprano_para_marcar():
    propuesta = proponer_marcacion([clase((8, 0), (9, 20))], momento(7, 0))
    assert propuesta["operacion"] is None
    assert "07:30" in propuesta["motivo"]


def test_clase_finalizada_no_admite_entrada():
    propuesta = proponer_marcacion([clase((8, 0), (9, 20))], momento(9, 30))
    assert propuesta["operacion"] is None
    assert "ya finalizó" in propuesta["motivo"]


def test_doble_pasada_tras_la_entrada_no_propone_salida():
    obligaciones = [clase((8, 0), (9, 20), entrada=momento(7, 58))]
    propuesta = proponer_marcacion(obligaciones, momento(8, 0))
    assert propuesta["operacion"] is None
    assert "Entrada ya registrada" in propuesta["motivo"]


def test_salida_anticipada_y_salida_normal():
    obligaciones = [clase((8, 0), (9, 20), entrada=momento(7, 58))]
    anticipada = proponer_marcacion(obligaciones, momento(9, 0))
    assert anticipada["operacion"] == SALIDA
    assert anticipada["items"][0]["salida_anticipada"] is True
    normal = proponer_marcacion(obligaciones, momento(9, 21))
    assert normal["items"][0]["salida_anticipada"] is False


def test_asistencia_completa():
    obligaciones = [
        clase((8, 0), (9, 20), entrada=momento(7, 58), salida=momento(9, 21))
    ]
    propuesta = proponer_marcacion(obligaciones, momento(9, 25))
    assert propuesta["operacion"] is None
    assert "Asistencia completa" in propuesta["motivo"]


def test_catedras_pegadas_comparten_entrada_y_salida():
    obligaciones = [
        clase((8, 0), (9, 20), "Programación I", id_=1),
        clase((9, 20), (10, 40), "Base de Datos", id_=2),
    ]
    entrada = proponer_marcacion(obligaciones, momento(7, 55))
    assert entrada["operacion"] == ENTRADA
    assert [i["horario_catedra_id"] for i in entrada["items"]] == [1, 2]
    assert not any(i["tardanza"] for i in entrada["items"])

    for o in obligaciones:
        o["entrada"] = momento(7, 55)
    salida = proponer_marcacion(obligaciones, momento(10, 0))
    assert salida["operacion"] == SALIDA
    assert [i["salida_anticipada"] for i in salida["items"]] == [False, True]


def test_catedras_separadas_se_marcan_por_separado():
    obligaciones = [
        clase((8, 0), (9, 20), "Programación I", id_=1),
        clase((14, 0), (15, 20), "Base de Datos", id_=2),
    ]
    entrada = proponer_marcacion(obligaciones, momento(7, 55))
    assert [i["horario_catedra_id"] for i in entrada["items"]] == [1]

    obligaciones[0]["entrada"] = momento(7, 55)
    obligaciones[0]["salida"] = momento(9, 20)
    tarde = proponer_marcacion(obligaciones, momento(13, 50))
    assert tarde["operacion"] == ENTRADA
    assert [i["horario_catedra_id"] for i in tarde["items"]] == [2]


def test_salida_olvidada_se_cierra_antes_de_la_nueva_entrada():
    obligaciones = [
        clase((8, 0), (9, 20), id_=1, entrada=momento(7, 55)),
        clase((14, 0), (15, 20), id_=2),
    ]
    propuesta = proponer_marcacion(obligaciones, momento(13, 50))
    assert propuesta["operacion"] == SALIDA
    assert propuesta["items"][0]["horario_catedra_id"] == 1


def test_actividad_especial_reemplaza_a_la_clase_superpuesta():
    obligaciones = [clase((8, 0), (9, 20), id_=1), actividad((8, 0), (12, 0))]
    vigentes, reemplazadas = separar_reemplazadas(obligaciones)
    assert [o["tipo"] for o in vigentes] == ["actividad"]
    assert [o["horario_catedra_id"] for o in reemplazadas] == [1]

    propuesta = proponer_marcacion(obligaciones, momento(7, 50))
    assert propuesta["operacion"] == ENTRADA
    assert [i["tipo"] for i in propuesta["items"]] == ["actividad"]


def test_entrada_a_mitad_de_bloque_solo_cubre_lo_que_no_termino():
    obligaciones = [
        clase((8, 0), (9, 20), id_=1),
        clase((9, 20), (10, 40), id_=2),
    ]
    propuesta = proponer_marcacion(obligaciones, momento(9, 22))
    assert [i["horario_catedra_id"] for i in propuesta["items"]] == [2]
    assert propuesta["items"][0]["tardanza"] is False
