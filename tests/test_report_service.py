import os
import sys
from datetime import date, datetime, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from openpyxl import load_workbook

from services import report_service, situacion_service

DOCENTE = {"apellido": "Pérez", "nombre": "Ana", "dni": "30111222", "cuil": "27301112223"}
DESDE, HASTA = date(2026, 11, 16), date(2026, 11, 20)
ENCABEZADO = report_service.datos_encabezado(DOCENTE, DESDE, HASTA, "admin", [(2026, 2, 6)])


def filas():
    obligaciones = [
        {
            "fecha": date(2026, 11, 16), "tipo": "clase", "descripcion": "Programación I",
            "inicio": time(8, 0), "fin": time(9, 20),
            "entrada": datetime(2026, 11, 16, 8, 10), "salida": None,
            "tardanza": True, "salida_anticipada": False,
        },
        {
            "fecha": date(2026, 11, 17), "tipo": "clase", "descripcion": "Base de Datos",
            "inicio": time(8, 0), "fin": time(9, 20), "entrada": None, "salida": None,
            "tardanza": False, "salida_anticipada": False,
        },
    ]
    ausencias = {date(2026, 11, 17): {"tipo": "particular", "estado": "registrada"}}
    return situacion_service.clasificar(obligaciones, ausencias, datetime(2026, 11, 20, 12, 0))


def textos_excel(ruta):
    hoja = load_workbook(ruta).active
    return [str(c.value) for fila in hoja.iter_rows() for c in fila if c.value is not None]


def test_nombre_sugerido():
    nombre = report_service.nombre_archivo_sugerido(DOCENTE, DESDE, HASTA, "pdf")
    assert nombre == "asistencia_Pérez_2026-11-16_a_2026-11-20.pdf"


def test_encabezado_incluye_particulares():
    assert ("Particulares 2026:", "2 de 6 utilizados") in ENCABEZADO


def test_excel_con_situaciones(tmp_path):
    ruta = str(tmp_path / "informe.xlsx")
    report_service.generar_excel(ruta, ENCABEZADO, filas())
    textos = textos_excel(ruta)
    assert "Pérez, Ana" in textos
    assert "Tardanza, Salida sin registrar" in textos
    assert "Ausente con aviso (particular)" in textos
    assert "Lunes" in textos
    assert "Obligaciones en el período" in textos


def test_excel_sin_obligaciones(tmp_path):
    ruta = str(tmp_path / "vacio.xlsx")
    report_service.generar_excel(ruta, ENCABEZADO, [])
    assert report_service.MENSAJE_SIN_OBLIGACIONES in textos_excel(ruta)


def test_pdf_se_genera(tmp_path):
    for nombre, datos in (("informe.pdf", filas()), ("vacio.pdf", [])):
        ruta = str(tmp_path / nombre)
        report_service.generar_pdf(ruta, ENCABEZADO, datos)
        with open(ruta, "rb") as archivo:
            assert archivo.read(5) == b"%PDF-"


def test_filas_actividades_incluye_catedra_roles_y_actividad_sin_docentes():
    from datetime import date, time

    mesa = {
        "tipo": "mesa_examen", "descripcion": "Final", "catedra": "Programación I",
        "fecha": date(2026, 12, 16), "hora_inicio": time(8, 0), "hora_fin": time(10, 0),
    }
    jornada = {
        "tipo": "jornada_institucional", "descripcion": "Jornada", "catedra": None,
        "fecha": date(2026, 11, 18), "hora_inicio": time(9, 0), "hora_fin": time(12, 0),
    }
    participantes = [{"apellido": "Rojas", "nombre": "Santiago", "rol": "presidente"}]
    filas = report_service.filas_actividades(
        [(mesa, participantes), (jornada, [])],
        {"mesa_examen": "Mesa de examen", "jornada_institucional": "Jornada institucional"},
        {"presidente": "Presidente"},
    )
    assert filas[0] == [
        "16/12/2026", "Miércoles", "08:00 - 10:00", "Mesa de examen",
        "Final (Programación I)", "Rojas, Santiago (Presidente)",
    ]
    assert filas[1][5] == "Sin docentes asignados"
