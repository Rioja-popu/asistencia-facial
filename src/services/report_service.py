import re
import unicodedata

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TITULO = "PLANILLA DE ASISTENCIA"
COLUMNAS = ["#", "Apellido", "Nombre", "DNI", "Libreta", "Entrada", "Salida"]
SIN_REGISTRAR = "Sin registrar"
MENSAJE_SIN_ASISTENCIAS = "No se registraron asistencias para esta Jornada."


def formatear_hora(valor):
    return valor.strftime("%H:%M") if valor is not None else SIN_REGISTRAR


def texto_contador(cantidad):
    if cantidad == 1:
        return "Se registró 1 alumno presente en total."
    return f"Se registraron {cantidad} alumnos presentes en total."


def nombre_sugerido(jornada, extension):
    """Ej.: asistencia_2026-10-08_reconocimiento-visual.xlsx"""
    sin_acentos = (
        unicodedata.normalize("NFKD", jornada["catedra"] or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    catedra = re.sub(r"[^a-z0-9]+", "-", sin_acentos.lower()).strip("-")
    partes = ["asistencia", jornada["fecha"].isoformat()]
    if catedra:
        partes.append(catedra)
    return "_".join(partes) + "." + extension


def datos_jornada(jornada):
    return [
        ("Fecha:", jornada["fecha"].strftime("%d/%m/%Y")),
        ("Cátedra:", jornada["catedra"]),
        ("Horario de entrada:", jornada["horario_entrada"].strftime("%H:%M")),
        ("Horario de salida:", jornada["horario_salida"].strftime("%H:%M")),
        ("Usuario:", jornada["nombre_usuario"]),
    ]


def filas_alumnos(asistencias):
    """asistencias = [(apellido, nombre, dni, libreta, entrada, salida), ...]"""
    return [
        [
            indice,
            apellido,
            nombre,
            dni,
            libreta,
            formatear_hora(entrada),
            formatear_hora(salida),
        ]
        for indice, (apellido, nombre, dni, libreta, entrada, salida) in enumerate(
            asistencias, start=1
        )
    ]


def generar_excel(ruta, jornada, asistencias):
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    negrita = Font(bold=True)
    borde = Border(*(Side(style="thin", color="999999"),) * 4)
    centrado = Alignment(horizontal="center")
    ultima_columna = len(COLUMNAS)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ultima_columna)
    ws["A1"] = TITULO
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = centrado

    fila = 3
    for etiqueta, valor in datos_jornada(jornada):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=2)
        ws.merge_cells(
            start_row=fila, start_column=3, end_row=fila, end_column=ultima_columna
        )
        ws.cell(row=fila, column=1, value=etiqueta).font = negrita
        ws.cell(row=fila, column=3, value=valor)
        fila += 1

    fila += 1
    filas = filas_alumnos(asistencias)
    if filas:
        for columna, titulo in enumerate(COLUMNAS, start=1):
            celda = ws.cell(row=fila, column=columna, value=titulo)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="2C3E50")
            celda.alignment = centrado
            celda.border = borde
        fila += 1
        for datos in filas:
            for columna, valor in enumerate(datos, start=1):
                celda = ws.cell(row=fila, column=columna, value=valor)
                celda.border = borde
                if columna in (1, 6, 7):
                    celda.alignment = centrado
            fila += 1
    else:
        ws.merge_cells(
            start_row=fila, start_column=1, end_row=fila, end_column=ultima_columna
        )
        ws.cell(row=fila, column=1, value=MENSAJE_SIN_ASISTENCIAS)
        fila += 1

    fila += 1
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima_columna)
    ws.cell(row=fila, column=1, value=texto_contador(len(filas))).font = negrita

    for letra, ancho in zip("ABCDEFG", (6, 24, 24, 14, 14, 12, 16)):
        ws.column_dimensions[letra].width = ancho

    wb.save(ruta)


def generar_pdf(ruta, jornada, asistencias):
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    celda = ParagraphStyle("celda", parent=normal, fontSize=9, leading=11)

    doc = SimpleDocTemplate(
        ruta,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=TITULO,
    )
    elementos = [Paragraph(TITULO, estilos["Title"]), Spacer(1, 0.4 * cm)]

    tabla_jornada = Table(
        [[etiqueta, Paragraph(valor, normal)] for etiqueta, valor in datos_jornada(jornada)],
        colWidths=[4.5 * cm, 12.5 * cm],
        hAlign="LEFT",
    )
    tabla_jornada.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elementos += [tabla_jornada, Spacer(1, 0.6 * cm)]

    filas = filas_alumnos(asistencias)
    if filas:
        datos = [COLUMNAS] + [
            [fila[0]] + [Paragraph(str(v), celda) for v in fila[1:5]] + fila[5:]
            for fila in filas
        ]
        tabla = Table(
            datos,
            colWidths=[c * cm for c in (1, 4.3, 4.3, 2.4, 2.2, 1.8, 2.6)],
            repeatRows=1,
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),
                    ("ALIGN", (5, 1), (6, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f2f4f5")],
                    ),
                ]
            )
        )
        elementos.append(tabla)
    else:
        elementos.append(Paragraph(MENSAJE_SIN_ASISTENCIAS, normal))

    elementos += [
        Spacer(1, 0.6 * cm),
        Paragraph(f"<b>{texto_contador(len(filas))}</b>", normal),
    ]
    doc.build(elementos)
