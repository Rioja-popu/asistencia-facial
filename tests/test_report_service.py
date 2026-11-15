import os
import sys
import tempfile
import unittest
from datetime import date, datetime, time

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from openpyxl import load_workbook

from services import report_service as rs

JORNADA = {
    "id": 1,
    "fecha": date(2026, 10, 8),
    "catedra": "Reconocimiento Visual",
    "horario_entrada": time(8, 0),
    "horario_salida": time(9, 20),
    "nombre_usuario": "marazsantiago",
}
ASISTENCIAS = [
    ("López", "Ana", "23456789", "A-002", datetime(2026, 10, 8, 8, 7), None),
    ("Pérez", "Juan", "12345678", "A-001", datetime(2026, 10, 8, 8, 3), datetime(2026, 10, 8, 9, 18)),
]


def textos_excel(ruta):
    ws = load_workbook(ruta).active
    return [[c for c in fila if c is not None] for fila in ws.iter_rows(values_only=True)]


class ReportServiceTest(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def ruta(self, nombre):
        return os.path.join(self.tmp.name, nombre)

    def test_nombre_sugerido(self):
        self.assertEqual(
            rs.nombre_sugerido(JORNADA, "xlsx"),
            "asistencia_2026-10-08_reconocimiento-visual.xlsx",
        )
        jornada = dict(JORNADA, catedra="Programación II / Álgebra")
        self.assertEqual(
            rs.nombre_sugerido(jornada, "pdf"),
            "asistencia_2026-10-08_programacion-ii-algebra.pdf",
        )

    def test_contador_singular_y_plural(self):
        self.assertEqual(rs.texto_contador(0), "Se registraron 0 alumnos presentes en total.")
        self.assertEqual(rs.texto_contador(1), "Se registró 1 alumno presente en total.")
        self.assertEqual(rs.texto_contador(8), "Se registraron 8 alumnos presentes en total.")

    def test_excel_con_asistencias(self):
        ruta = self.ruta("informe.xlsx")
        rs.generar_excel(ruta, JORNADA, ASISTENCIAS)
        filas = textos_excel(ruta)
        self.assertIn(["PLANILLA DE ASISTENCIA"], filas)
        self.assertIn(["Fecha:", "08/10/2026"], filas)
        self.assertIn(["Cátedra:", "Reconocimiento Visual"], filas)
        self.assertIn(["Horario de entrada:", "08:00"], filas)
        self.assertIn(["Horario de salida:", "09:20"], filas)
        self.assertIn(["Usuario:", "marazsantiago"], filas)
        self.assertIn(rs.COLUMNAS, filas)
        self.assertIn([1, "López", "Ana", "23456789", "A-002", "08:07", "Sin registrar"], filas)
        self.assertIn([2, "Pérez", "Juan", "12345678", "A-001", "08:03", "09:18"], filas)
        self.assertEqual(filas[-1], ["Se registraron 2 alumnos presentes en total."])

    def test_excel_sin_asistencias(self):
        ruta = self.ruta("vacio.xlsx")
        rs.generar_excel(ruta, JORNADA, [])
        filas = textos_excel(ruta)
        self.assertIn([rs.MENSAJE_SIN_ASISTENCIAS], filas)
        self.assertNotIn(rs.COLUMNAS, filas)
        self.assertEqual(filas[-1], ["Se registraron 0 alumnos presentes en total."])

    def test_pdf_se_genera(self):
        for nombre, asistencias in (("con.pdf", ASISTENCIAS), ("sin.pdf", [])):
            ruta = self.ruta(nombre)
            rs.generar_pdf(ruta, JORNADA, asistencias)
            with open(ruta, "rb") as archivo:
                self.assertEqual(archivo.read(5), b"%PDF-")


if __name__ == "__main__":
    unittest.main()
