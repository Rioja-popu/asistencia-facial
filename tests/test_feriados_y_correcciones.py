import os
import sys
from datetime import date, datetime, time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openpyxl import load_workbook

from services import marcacion_service as m
from services import report_service
from services import situacion_service as s

DIA = date(2026, 11, 20)
FERIADO = "Feriado: Día de la Soberanía Nacional"


def obligacion(tipo="clase", no_laborable=None, entrada=None, salida=None, fecha=DIA,
               tardanza=False, motivo=None):
    return {
        "fecha": fecha, "tipo": tipo, "descripcion": "Programación I",
        "horario_catedra_id": 1 if tipo == "clase" else None,
        "actividad_docente_id": None if tipo == "clase" else 1,
        "inicio": time(8, 0), "fin": time(9, 20),
        "asistencia_id": 7 if entrada else None, "entrada": entrada, "salida": salida,
        "tardanza": tardanza, "salida_anticipada": False,
        "no_laborable": no_laborable, "motivo_correccion": motivo,
    }


# ------------------------------------------------------------ feriados y recesos
def test_en_feriado_no_se_propone_marcar_la_clase():
    propuesta = m.proponer_marcacion([obligacion(no_laborable=FERIADO)], datetime(2026, 11, 20, 8, 0))
    assert propuesta["operacion"] is None
    assert FERIADO in propuesta["motivo"]


def test_en_feriado_la_mesa_de_examen_se_mantiene():
    obligaciones = [obligacion(no_laborable=FERIADO), obligacion(tipo="actividad")]
    propuesta = m.proponer_marcacion(obligaciones, datetime(2026, 11, 20, 8, 0))
    assert propuesta["operacion"] == m.ENTRADA
    assert [o["tipo"] for o in propuesta["items"]] == ["actividad"]


def test_clase_en_feriado_no_es_ausencia():
    filas = s.clasificar([obligacion(no_laborable=FERIADO)], {}, datetime(2026, 11, 23, 12, 0))
    assert filas[0]["situacion"] == f"Sin clases ({FERIADO})"
    assert s.AUSENTE_SIN_AVISO not in filas[0]["etiquetas"]
    assert s.exigibles(filas) == []


def test_clase_marcada_en_feriado_se_sigue_mostrando():
    marcada = obligacion(no_laborable=FERIADO, entrada=datetime(2026, 11, 20, 8, 0),
                         salida=datetime(2026, 11, 20, 9, 20))
    filas = s.clasificar([marcada], {}, datetime(2026, 11, 23, 12, 0))
    assert filas[0]["situacion"] == s.EN_HORARIO


# ---------------------------------------------------------- corrección manual
def test_correccion_recalcula_tardanza_y_salida_anticipada():
    c = m.preparar_correccion(DIA, time(8, 0), time(9, 20), time(8, 6), time(9, 0))
    assert c["entrada"] == datetime(2026, 11, 20, 8, 6)
    assert c["tardanza"] and c["salida_anticipada"]
    c = m.preparar_correccion(DIA, time(8, 0), time(9, 20), time(7, 55), time(9, 20))
    assert not c["tardanza"] and not c["salida_anticipada"]


def test_correccion_sin_salida():
    c = m.preparar_correccion(DIA, time(8, 0), time(9, 20), time(8, 0), None)
    assert c["salida"] is None and not c["salida_anticipada"]


@pytest.mark.parametrize("entrada, salida", [
    (time(9, 0), time(8, 30)),   # salida anterior a la entrada
    (time(7, 0), time(9, 20)),   # entrada más de 30 minutos antes
    (time(9, 30), time(10, 0)),  # entrada posterior al fin previsto
])
def test_correccion_rechaza_horas_incoherentes(entrada, salida):
    with pytest.raises(ValueError):
        m.preparar_correccion(DIA, time(8, 0), time(9, 20), entrada, salida)


def test_la_correccion_figura_en_el_informe():
    corregida = obligacion(entrada=datetime(2026, 11, 20, 8, 0), salida=datetime(2026, 11, 20, 9, 20),
                           motivo="se olvidó de marcar la salida")
    fila = s.clasificar([corregida], {}, datetime(2026, 11, 23, 12, 0))[0]
    assert fila["situacion"] == "En horario [corregida a mano: se olvidó de marcar la salida]"
    assert s.CORREGIDA in fila["etiquetas"]
    assert fila["asistencia_id"] == 7 and fila["horario_catedra_id"] == 1


# ------------------------------------------------------------ resumen general
def resumenes():
    ahora = datetime(2026, 11, 23, 12, 0)
    ana = s.clasificar(
        [
            obligacion(fecha=date(2026, 11, 16), entrada=datetime(2026, 11, 16, 8, 10),
                       salida=datetime(2026, 11, 16, 9, 20), tardanza=True),
            obligacion(fecha=date(2026, 11, 17)),
            obligacion(fecha=date(2026, 11, 18)),
            obligacion(no_laborable=FERIADO),
        ],
        {date(2026, 11, 17): {"tipo": "particular", "estado": "registrada"}},
        ahora,
    )
    return [
        ({"apellido": "Pérez", "nombre": "Ana"}, ana, "1 de 6"),
        ({"apellido": "Sin", "nombre": "Horarios"}, [], "0 de 6"),
    ]


def test_resumen_general_cuenta_por_docente_y_omite_a_quien_no_tiene_obligaciones():
    filas = report_service.filas_general(resumenes())
    # Docente, obligaciones (sin el feriado), en horario, tardanzas, salidas anticipadas,
    # salidas sin registrar, con aviso, sin aviso, médica no justificada, particulares
    assert filas == [["Pérez, Ana", 3, 0, 1, 0, 0, 1, 1, 0, "1 de 6"]]
    assert report_service.fila_totales_general(filas) == ["Total", 3, 0, 1, 0, 0, 1, 1, 0, ""]


def test_resumen_general_en_excel_y_pdf(tmp_path):
    filas = report_service.filas_general(resumenes())
    encabezado = report_service.encabezado_general(date(2026, 11, 16), date(2026, 11, 20), "admin")
    ruta = str(tmp_path / "resumen.xlsx")
    report_service.generar_excel_general(ruta, encabezado, filas)
    hoja = load_workbook(ruta).active
    textos = [c.value for fila in hoja.iter_rows() for c in fila if c.value is not None]
    assert "Pérez, Ana" in textos and "Total" in textos and "16/11/2026 al 20/11/2026" in textos
    for datos in (filas, []):
        pdf = str(tmp_path / f"resumen{len(datos)}.pdf")
        report_service.generar_pdf_general(pdf, encabezado, datos)
        assert os.path.getsize(pdf) > 1000
