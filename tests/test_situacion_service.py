import os
import sys
from datetime import date, datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from services import situacion_service as s

DIA = date(2026, 11, 16)
AHORA = datetime(2026, 11, 20, 12, 0)


def obligacion(entrada=None, salida=None, tardanza=False, anticipada=False,
               tipo="clase", inicio=(8, 0), fin=(9, 20), fecha=DIA):
    return {
        "fecha": fecha, "tipo": tipo, "descripcion": "Programación I",
        "inicio": time(*inicio), "fin": time(*fin),
        "entrada": entrada, "salida": salida,
        "tardanza": tardanza, "salida_anticipada": anticipada,
    }


def situacion(o, ausencias=None, ahora=AHORA):
    return s.clasificar([o], ausencias or {}, ahora)[0]["situacion"]


def test_presente_en_horario_con_salida_normal():
    o = obligacion(datetime(2026, 11, 16, 7, 58), datetime(2026, 11, 16, 9, 20))
    assert situacion(o) == s.EN_HORARIO


def test_tardanza_y_salida_anticipada():
    o = obligacion(datetime(2026, 11, 16, 8, 10), datetime(2026, 11, 16, 9, 0),
                   tardanza=True, anticipada=True)
    assert situacion(o) == "Tardanza, Salida anticipada"


def test_salida_sin_registrar():
    o = obligacion(datetime(2026, 11, 16, 7, 58))
    assert situacion(o) == "En horario, Salida sin registrar"
    assert situacion(o, ahora=datetime(2026, 11, 16, 8, 30)) == "En horario, En curso"


def test_ausente_sin_aviso_y_programada():
    assert situacion(obligacion()) == s.AUSENTE_SIN_AVISO
    assert situacion(obligacion(), ahora=datetime(2026, 11, 16, 7, 0)) == s.PROGRAMADA


def test_ausente_con_aviso():
    particular = {DIA: {"tipo": "particular", "estado": "registrada"}}
    assert situacion(obligacion(), particular) == "Ausente con aviso (particular)"
    pendiente = {DIA: {"tipo": "medica", "estado": "pendiente_certificado"}}
    assert "certificado pendiente" in situacion(obligacion(), pendiente)
    justificada = {DIA: {"tipo": "medica", "estado": "justificada"}}
    assert situacion(obligacion(), justificada) == "Ausente con aviso (médica justificada)"
    rechazada = {DIA: {"tipo": "medica", "estado": "no_justificada"}}
    assert situacion(obligacion(), rechazada) == s.AUSENCIA_NO_JUSTIFICADA


def test_clase_reemplazada_por_actividad():
    clase = obligacion()
    mesa = obligacion(tipo="actividad", inicio=(8, 0), fin=(12, 0))
    filas = s.clasificar([clase, mesa], {}, AHORA)
    assert [f["situacion"] for f in filas] == [s.REEMPLAZADA, s.AUSENTE_SIN_AVISO]


def test_totales():
    filas = s.clasificar(
        [
            obligacion(datetime(2026, 11, 16, 8, 10), tardanza=True),
            obligacion(fecha=date(2026, 11, 17)),
        ],
        {},
        AHORA,
    )
    assert s.totales(filas) == [
        (s.TARDANZA, 1), (s.SALIDA_SIN_REGISTRAR, 1), (s.AUSENTE_SIN_AVISO, 1),
    ]
