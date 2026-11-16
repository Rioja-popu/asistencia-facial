"""Informe de asistencia de un docente en un período, en Excel y PDF.

Recibe las filas ya clasificadas por situacion_service; no accede a la base.
"""

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services import situacion_service

INSTITUCION = "IES N.º 7 Populorum Progressio"
TITULO = "Informe de asistencia docente"
COLUMNAS = ["Fecha", "Día", "Obligación", "Horario previsto", "Entrada", "Salida", "Situación"]
MENSAJE_SIN_OBLIGACIONES = "El docente no tiene obligaciones en el período seleccionado."
AZUL = "143560"
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def formatear_fecha(fecha):
    return fecha.strftime("%d/%m/%Y")


def formatear_hora(momento):
    return momento.strftime("%H:%M") if momento else "-"


def nombre_archivo_sugerido(docente, desde, hasta, extension):
    apellido = "".join(c if c.isalnum() else "_" for c in docente["apellido"])
    return f"asistencia_{apellido}_{desde:%Y-%m-%d}_a_{hasta:%Y-%m-%d}.{extension}"


def datos_encabezado(docente, desde, hasta, usuario, particulares):
    """particulares: [(año, usados, límite), ...]"""
    datos = [
        ("Docente:", f"{docente['apellido']}, {docente['nombre']}"),
        ("DNI / CUIL:", f"{docente['dni'] or 'Sin cargar'} / {docente['cuil'] or 'Sin cargar'}"),
        ("Período:", f"{formatear_fecha(desde)} al {formatear_fecha(hasta)}"),
    ]
    for anio, usados, limite in particulares:
        datos.append((f"Particulares {anio}:", f"{usados} de {limite} utilizados"))
    datos.append(("Informe generado por:", usuario))
    return datos


def filas_informe(filas):
    return [
        [
            formatear_fecha(f["fecha"]),
            DIAS[f["fecha"].weekday()],
            f["descripcion"],
            f"{formatear_hora(f['inicio'])} - {formatear_hora(f['fin'])}",
            formatear_hora(f["entrada"]),
            formatear_hora(f["salida"]),
            f["situacion"],
        ]
        for f in filas
    ]


def filas_totales(filas):
    return [("Obligaciones en el período", len(filas))] + situacion_service.totales(filas)


def generar_excel(ruta, encabezado, filas):
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    negrita = Font(bold=True)
    borde = Border(*(Side(style="thin", color="999999"),) * 4)
    centrado = Alignment(horizontal="center")
    ultima = len(COLUMNAS)

    for fila, texto, tamano in ((1, INSTITUCION, 14), (2, TITULO, 12)):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima)
        celda = ws.cell(row=fila, column=1, value=texto)
        celda.font = Font(bold=True, size=tamano, color=AZUL)
        celda.alignment = centrado

    fila = 4
    for etiqueta, valor in encabezado:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=2)
        ws.merge_cells(start_row=fila, start_column=3, end_row=fila, end_column=ultima)
        ws.cell(row=fila, column=1, value=etiqueta).font = negrita
        ws.cell(row=fila, column=3, value=valor)
        fila += 1

    fila += 1
    detalle = filas_informe(filas)
    if detalle:
        for columna, titulo in enumerate(COLUMNAS, start=1):
            celda = ws.cell(row=fila, column=columna, value=titulo)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor=AZUL)
            celda.alignment = centrado
            celda.border = borde
        fila += 1
        for datos in detalle:
            for columna, valor in enumerate(datos, start=1):
                celda = ws.cell(row=fila, column=columna, value=valor)
                celda.border = borde
                if columna in (1, 4, 5, 6):
                    celda.alignment = centrado
            fila += 1
    else:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima)
        ws.cell(row=fila, column=1, value=MENSAJE_SIN_OBLIGACIONES)
        fila += 1

    fila += 1
    ws.cell(row=fila, column=1, value="Resumen").font = negrita
    fila += 1
    for nombre, cantidad in filas_totales(filas):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=3)
        ws.cell(row=fila, column=1, value=nombre)
        ws.cell(row=fila, column=4, value=cantidad).alignment = centrado
        fila += 1

    for letra, ancho in zip("ABCDEFG", (12, 12, 48, 17, 10, 10, 48)):
        ws.column_dimensions[letra].width = ancho

    wb.save(ruta)


def generar_pdf(ruta, encabezado, filas, ruta_escudo=None):
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    celda = ParagraphStyle("celda", parent=normal, fontSize=8, leading=10)
    azul = colors.HexColor("#" + AZUL)
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=azul, fontSize=16)
    subtitulo = ParagraphStyle(
        "subtitulo", parent=estilos["Heading2"], textColor=azul, alignment=1
    )

    doc = SimpleDocTemplate(
        ruta,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=TITULO,
    )
    elementos = []
    if ruta_escudo:
        elementos.append(Image(ruta_escudo, width=2.2 * cm, height=2.2 * cm))
    elementos += [
        Paragraph(INSTITUCION, titulo),
        Paragraph(TITULO, subtitulo),
        Spacer(1, 0.3 * cm),
    ]

    tabla_encabezado = Table(
        [[etiqueta, Paragraph(str(valor), normal)] for etiqueta, valor in encabezado],
        colWidths=[4.5 * cm, 20 * cm],
        hAlign="LEFT",
    )
    tabla_encabezado.setStyle(
        TableStyle(
            [("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("VALIGN", (0, 0), (-1, -1), "TOP")]
        )
    )
    elementos += [tabla_encabezado, Spacer(1, 0.5 * cm)]

    detalle = filas_informe(filas)
    if detalle:
        datos = [COLUMNAS] + [
            [f[0], f[1], Paragraph(f[2], celda), f[3], f[4], f[5], Paragraph(f[6], celda)]
            for f in detalle
        ]
        tabla = Table(
            datos,
            colWidths=[c * cm for c in (2.2, 2.2, 8.4, 3, 1.7, 1.7, 7.3)],
            repeatRows=1,
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), azul),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (3, 1), (5, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f9")]),
                ]
            )
        )
        elementos.append(tabla)
    else:
        elementos.append(Paragraph(MENSAJE_SIN_OBLIGACIONES, normal))

    resumen = Table(
        [["Resumen", ""]] + [[n, str(c)] for n, c in filas_totales(filas)],
        colWidths=[8 * cm, 2 * cm],
        hAlign="LEFT",
    )
    resumen.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, azul),
            ]
        )
    )
    elementos += [Spacer(1, 0.5 * cm), resumen]
    doc.build(elementos)


# ------------------------------------------------------- actividades especiales
TITULO_ACTIVIDADES = "Actividades especiales"
COLUMNAS_ACTIVIDADES = ["Fecha", "Día", "Horario", "Tipo", "Descripción", "Docentes"]
MENSAJE_SIN_ACTIVIDADES = "No hay actividades especiales registradas."


def filas_actividades(actividades, tipos, roles):
    """actividades: [(actividad, participantes), ...] en el orden a mostrar."""
    filas = []
    for actividad, participantes in actividades:
        descripcion = actividad["descripcion"]
        if actividad.get("catedra"):
            descripcion += f" ({actividad['catedra']})"
        docentes = []
        for p in participantes:
            nombre = f"{p['apellido']}, {p['nombre']}"
            if p.get("rol"):
                nombre += f" ({roles.get(p['rol'], p['rol'])})"
            docentes.append(nombre)
        filas.append(
            [
                formatear_fecha(actividad["fecha"]),
                DIAS[actividad["fecha"].weekday()],
                f"{formatear_hora(actividad['hora_inicio'])} - "
                f"{formatear_hora(actividad['hora_fin'])}",
                tipos.get(actividad["tipo"], actividad["tipo"]),
                descripcion,
                "; ".join(docentes) if docentes else "Sin docentes asignados",
            ]
        )
    return filas


def _texto_total_actividades(filas):
    cantidad = len(filas)
    return f"Total: {cantidad} actividad" + ("" if cantidad == 1 else "es")


def generar_excel_actividades(ruta, filas, usuario):
    wb = Workbook()
    ws = wb.active
    ws.title = "Actividades"
    borde = Border(*(Side(style="thin", color="999999"),) * 4)
    centrado = Alignment(horizontal="center", vertical="top")
    ultima = len(COLUMNAS_ACTIVIDADES)

    for fila, texto, tamano in ((1, INSTITUCION, 14), (2, TITULO_ACTIVIDADES, 12)):
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima)
        celda = ws.cell(row=fila, column=1, value=texto)
        celda.font = Font(bold=True, size=tamano, color=AZUL)
        celda.alignment = Alignment(horizontal="center")
    ws.cell(row=4, column=1, value="Generado por:").font = Font(bold=True)
    ws.cell(row=4, column=3, value=usuario)

    fila = 6
    if filas:
        for columna, titulo in enumerate(COLUMNAS_ACTIVIDADES, start=1):
            celda = ws.cell(row=fila, column=columna, value=titulo)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor=AZUL)
            celda.alignment = Alignment(horizontal="center")
            celda.border = borde
        fila += 1
        for datos in filas:
            for columna, valor in enumerate(datos, start=1):
                celda = ws.cell(row=fila, column=columna, value=valor)
                celda.border = borde
                celda.alignment = (
                    centrado if columna <= 3 else Alignment(wrap_text=True, vertical="top")
                )
            fila += 1
        fila += 1
        ws.cell(row=fila, column=1, value=_texto_total_actividades(filas)).font = Font(bold=True)
    else:
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima)
        ws.cell(row=fila, column=1, value=MENSAJE_SIN_ACTIVIDADES)

    for letra, ancho in zip("ABCDEF", (12, 12, 15, 22, 45, 60)):
        ws.column_dimensions[letra].width = ancho
    wb.save(ruta)


def generar_pdf_actividades(ruta, filas, usuario, ruta_escudo=None):
    estilos = getSampleStyleSheet()
    normal = estilos["Normal"]
    celda = ParagraphStyle("celda", parent=normal, fontSize=8, leading=10)
    azul = colors.HexColor("#" + AZUL)
    titulo = ParagraphStyle("titulo", parent=estilos["Title"], textColor=azul, fontSize=16)
    subtitulo = ParagraphStyle(
        "subtitulo", parent=estilos["Heading2"], textColor=azul, alignment=1
    )
    doc = SimpleDocTemplate(
        ruta,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title=TITULO_ACTIVIDADES,
    )
    elementos = []
    if ruta_escudo:
        elementos.append(Image(ruta_escudo, width=2.2 * cm, height=2.2 * cm))
    elementos += [
        Paragraph(INSTITUCION, titulo),
        Paragraph(TITULO_ACTIVIDADES, subtitulo),
        Paragraph(f"<b>Generado por:</b> {usuario}", normal),
        Spacer(1, 0.5 * cm),
    ]
    if filas:
        datos = [COLUMNAS_ACTIVIDADES] + [
            [f[0], f[1], f[2], Paragraph(f[3], celda), Paragraph(f[4], celda), Paragraph(f[5], celda)]
            for f in filas
        ]
        tabla = Table(
            datos,
            colWidths=[c * cm for c in (2.2, 2.2, 2.8, 3.6, 7.2, 8.5)],
            repeatRows=1,
        )
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), azul),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (0, 1), (2, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef3f9")]),
                ]
            )
        )
        elementos += [tabla, Spacer(1, 0.4 * cm), Paragraph(_texto_total_actividades(filas), normal)]
    else:
        elementos.append(Paragraph(MENSAJE_SIN_ACTIVIDADES, normal))
    doc.build(elementos)
