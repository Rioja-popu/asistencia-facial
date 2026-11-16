"""Importación de horarios desde la planilla modelo (el cuadro de horarios del instituto).

Cada hoja es un curso: arriba la carrera y el curso, debajo una grilla con los
módulos en filas y los días en columnas. Cada celda dice
"MATERIA - APELLIDO, NOMBRE". No accede a la base: `leer_planilla` devuelve los
bloques leídos y `planificar` decide qué se crearía con los datos ya cargados.
"""

import re
import unicodedata
from datetime import datetime, time

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

MINUTOS_CLASE = 80  # Una clase dura 1 h 20 min: es el mínimo de un horario
MINUTOS_MODULO = 40  # El cuadro del instituto se arma en módulos de 40 min
DIAS = {
    "lunes": 1, "martes": 2, "miercoles": 3, "jueves": 4,
    "viernes": 5, "sabado": 6, "domingo": 7,
}
NOMBRES_DIAS = {
    1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves",
    5: "Viernes", 6: "Sábado", 7: "Domingo",
}
ETIQUETAS = {"carrera", "curso", "coordinador", "turno", "comision"}
MODULOS_MODELO = [
    "8:00 a 8:40", "8:40 a 9:20", "9:20 a 10:00", "10:00 a 10:40",
    "10:40 a 11:20", "11:20 a 12:00", "12:00 a 12:40", "12:40 a 13:20",
]
HOJA_INSTRUCCIONES = "Instrucciones"
INSTRUCCIONES = [
    "Cómo completar la planilla",
    "1. Usá una hoja por curso (carrera + año). Para otro curso, duplicá la hoja "
    "\"Curso\" y cambiale el nombre.",
    "2. Completá CARRERA y CURSO (1ro, 2do, 3ro...). Coordinador, turno y comisión "
    "son opcionales y no se importan.",
    "3. En cada celda escribí la materia y el docente así: "
    "MATERIA - APELLIDO, NOMBRE. Ejemplo: ANALÍTICA WEB - MARAZ, SANTIAGO FEDERICO",
    "4. Escribí el nombre del docente siempre igual: es lo que usa el sistema para "
    "reconocer que es la misma persona.",
    "5. Los módulos seguidos de la misma materia y docente se unen en un solo horario.",
    "6. Podés cambiar los horarios de la primera columna (formato \"8:00 a 8:40\") "
    "y agregar filas o la columna SÁBADO.",
    "7. Esta hoja de instrucciones no se importa.",
]

_HORARIO = re.compile(r"(\d{1,2})[:.](\d{2})\s*(?:a|-|–|hasta)\s*(\d{1,2})[:.](\d{2})", re.I)
_SEPARADOR = re.compile(r"\s+[-–]\s+")


def normalizar(texto):
    """Clave para comparar nombres sin importar mayúsculas, tildes ni espacios."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())


def duracion_valida(minutos):
    return minutos >= MINUTOS_CLASE and minutos % MINUTOS_MODULO == 0


def _limpio(valor):
    return " ".join(str(valor).split()) if valor is not None else ""


def _nombre_propio(texto):
    return texto.title() if texto.isupper() else texto


def _minutos(inicio, fin):
    return (fin.hour * 60 + fin.minute) - (inicio.hour * 60 + inicio.minute)


def _rango(bloque):
    return f"{bloque['inicio']:%H:%M} - {bloque['fin']:%H:%M}"


# ---------- Planilla modelo ----------

def generar_planilla(ruta):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Curso"
    negrita = Font(bold=True)
    gris = PatternFill("solid", start_color="D9D9D9")
    celeste = PatternFill("solid", start_color="9FE2F0")
    linea = Side(style="thin")
    borde = Border(left=linea, right=linea, top=linea, bottom=linea)
    centro = Alignment(horizontal="center", vertical="center", wrap_text=True)

    hoja.merge_cells("A1:F1")
    hoja["A1"] = "HORARIOS CICLO LECTIVO"
    hoja["A1"].font = Font(bold=True, size=13)
    hoja["A1"].alignment = centro
    for celda, texto in (
        ("A3", "CARRERA"), ("D3", "CURSO"), ("F3", "COMISION"),
        ("A4", "COORDINADOR"), ("D4", "TURNO"),
    ):
        hoja[celda] = texto
        hoja[celda].fill = gris
    hoja.merge_cells("B3:C3")
    hoja.merge_cells("B4:C4")
    for fila in (3, 4):
        for columna in range(1, 7):
            celda = hoja.cell(row=fila, column=columna)
            celda.border = borde
            celda.font = negrita
            celda.alignment = centro

    encabezados = ["HORARIOS", "LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES"]
    for columna, texto in enumerate(encabezados, start=1):
        celda = hoja.cell(row=6, column=columna, value=texto)
        celda.font = negrita
        celda.fill = gris
        celda.border = borde
        celda.alignment = centro
    for i, modulo in enumerate(MODULOS_MODELO):
        fila = 7 + i
        hoja.row_dimensions[fila].height = 42
        for columna in range(1, 7):
            celda = hoja.cell(row=fila, column=columna)
            celda.border = borde
            celda.alignment = centro
        hoja.cell(row=fila, column=1, value=modulo).fill = celeste
    hoja.column_dimensions["A"].width = 16
    for letra in "BCDEF":
        hoja.column_dimensions[letra].width = 30

    ayuda = libro.create_sheet(HOJA_INSTRUCCIONES)
    ayuda.column_dimensions["A"].width = 110
    for i, texto in enumerate(INSTRUCCIONES, start=1):
        celda = ayuda.cell(row=i, column=1, value=texto)
        celda.alignment = Alignment(wrap_text=True, vertical="top")
        if i == 1:
            celda.font = Font(bold=True, size=13)
    libro.save(ruta)


# ---------- Lectura ----------

def _valores(hoja):
    """{(fila, columna): texto}, repitiendo el valor en las celdas combinadas."""
    valores = {}
    for fila in hoja.iter_rows():
        for celda in fila:
            texto = _limpio(celda.value)
            if isinstance(celda.value, (time, datetime)):
                texto = celda.value.strftime("%H:%M")
            if texto:
                valores[(celda.row, celda.column)] = texto
    for rango in hoja.merged_cells.ranges:
        texto = valores.get((rango.min_row, rango.min_col))
        if texto:
            for fila in range(rango.min_row, rango.max_row + 1):
                for columna in range(rango.min_col, rango.max_col + 1):
                    valores[(fila, columna)] = texto
    return valores


def _dato_encabezado(valores, etiqueta, hasta_fila):
    for (fila, columna), texto in sorted(valores.items()):
        if fila >= hasta_fila or normalizar(texto) != etiqueta:
            continue
        derecha = sorted(
            (c, t) for (f, c), t in valores.items() if f == fila and c > columna
        )
        for _, candidato in derecha:
            if normalizar(candidato) == etiqueta:
                continue
            return "" if normalizar(candidato) in ETIQUETAS else candidato
    return ""


def _leer_celda(texto):
    """Devuelve (catedra, apellido, nombre) o None si no respeta el formato."""
    partes = _SEPARADOR.split(texto)
    if len(partes) < 2 or "," not in partes[-1]:
        return None
    apellido, nombre = (p.strip() for p in partes[-1].split(",", 1))
    catedra = texto[: texto.rfind(partes[-1])]
    catedra = _SEPARADOR.sub(" - ", catedra).strip(" -–")
    if not (catedra and apellido and nombre):
        return None
    return catedra, _nombre_propio(apellido), _nombre_propio(nombre)


def _leer_hoja(hoja):
    valores = _valores(hoja)
    filas_dias = {}
    for (fila, columna), texto in valores.items():
        if normalizar(texto) in DIAS:
            filas_dias.setdefault(fila, {})[columna] = DIAS[normalizar(texto)]
    if not filas_dias:
        return [], []  # No es una hoja de horarios (por ejemplo, las instrucciones)
    fila_dias = min(filas_dias)
    columnas = filas_dias[fila_dias]
    primera_columna = min(columnas)
    donde = f"Hoja \"{hoja.title}\""

    errores = []
    carrera = _dato_encabezado(valores, "carrera", fila_dias)
    curso = _dato_encabezado(valores, "curso", fila_dias)
    anio = re.search(r"[1-6]", curso)
    if not carrera:
        errores.append(f"{donde}: falta el nombre de la carrera.")
    if not anio:
        errores.append(f"{donde}: falta el curso (1ro a 6to).")
    if errores:
        return [], errores

    modulos = []
    for fila in range(fila_dias + 1, hoja.max_row + 1):
        izquierda = [valores.get((fila, c), "") for c in range(1, primera_columna)]
        if any(normalizar(t).startswith("observacion") for t in izquierda):
            break
        celdas = {dia: valores.get((fila, c), "") for c, dia in columnas.items()}
        horario = next((m for m in map(_HORARIO.search, izquierda) if m), None)
        if not horario:
            if any(celdas.values()):
                errores.append(f"{donde}, fila {fila}: no se entiende el horario del módulo.")
            continue
        try:
            inicio = time(int(horario[1]), int(horario[2]))
            fin = time(int(horario[3]), int(horario[4]))
        except ValueError:
            inicio = fin = None
        if inicio is None or fin <= inicio:
            errores.append(f"{donde}, fila {fila}: el horario del módulo no es válido.")
            continue
        modulos.append((fila, inicio, fin, celdas))

    bloques = []
    for dia in sorted(set(columnas.values())):
        abierto = None
        for fila, inicio, fin, celdas in sorted(modulos, key=lambda m: m[1]):
            texto = celdas[dia]
            if not texto:
                abierto = None
                continue
            datos = _leer_celda(texto)
            if datos is None:
                errores.append(
                    f"{donde}, {NOMBRES_DIAS[dia]} fila {fila}: \"{texto}\" no tiene el "
                    "formato MATERIA - APELLIDO, NOMBRE."
                )
                abierto = None
                continue
            clave = tuple(normalizar(d) for d in datos)
            if abierto and abierto["clave"] == clave and abierto["fin"] == inicio:
                abierto["fin"] = fin
                continue
            abierto = {
                "hoja": hoja.title, "carrera": carrera, "anio": int(anio[0]),
                "catedra": datos[0], "apellido": datos[1], "nombre": datos[2],
                "dia": dia, "inicio": inicio, "fin": fin, "clave": clave,
            }
            bloques.append(abierto)
    for bloque in bloques:
        del bloque["clave"]
    return bloques, errores


def leer_planilla(ruta):
    """Devuelve (bloques, errores). Un bloque es un horario semanal ya unido."""
    libro = load_workbook(ruta, data_only=True)
    bloques, errores = [], []
    for hoja in libro.worksheets:
        nuevos, fallas = _leer_hoja(hoja)
        bloques += nuevos
        errores += fallas
    if not bloques and not errores:
        errores.append("El archivo no tiene ninguna hoja con el cuadro de horarios.")
    return bloques, errores


# ---------- Plan de importación ----------

def planificar(bloques, carreras, catedras, docentes, horarios):
    """Compara lo leído con lo que ya está cargado.

    carreras  [{id, nombre}]
    catedras  [{id, nombre, anio, carrera}]
    docentes  [{id, apellido, nombre}]
    horarios  horarios vigentes: [{docente_id, catedra_id, dia_semana, hora_inicio, hora_fin}]

    Devuelve un dict con:
        horarios          bloques a crear, con carrera_id / catedra_id / docente_id
                          (None cuando hay que crearlos)
        carreras_nuevas, catedras_nuevas, docentes_nuevos   textos para mostrar
        omitidos          bloques que ya estaban cargados
        errores           [(bloque, motivo)]
    """
    ids_carrera = {normalizar(c["nombre"]): c["id"] for c in carreras}
    ids_catedra = {
        (normalizar(c["carrera"]), normalizar(c["nombre"])): c["id"] for c in catedras
    }
    por_nombre = {}
    for d in docentes:
        clave = (normalizar(d["apellido"]), normalizar(d["nombre"]))
        por_nombre.setdefault(clave, []).append(d["id"])
    ocupados = {}  # (clave docente, día) -> [(inicio, fin, descripción, catedra_id)]
    claves_por_id = {i: clave for clave, ids in por_nombre.items() for i in ids}
    nombres_catedra = {c["id"]: c["nombre"] for c in catedras}
    for h in horarios:
        clave = claves_por_id.get(h["docente_id"])
        if clave:
            ocupados.setdefault((clave, h["dia_semana"]), []).append(
                (h["hora_inicio"], h["hora_fin"],
                 nombres_catedra.get(h["catedra_id"], "otra cátedra"), h["catedra_id"])
            )

    plan = {
        "horarios": [], "omitidos": [], "errores": [],
        "carreras_nuevas": [], "catedras_nuevas": [], "docentes_nuevos": [],
    }
    for bloque in bloques:
        clave_docente = (normalizar(bloque["apellido"]), normalizar(bloque["nombre"]))
        clave_carrera = normalizar(bloque["carrera"])
        clave_catedra = (clave_carrera, normalizar(bloque["catedra"]))
        catedra_id = ids_catedra.get(clave_catedra)
        if len(por_nombre.get(clave_docente, [])) > 1:
            plan["errores"].append(
                (bloque, "Hay más de un docente cargado con ese apellido y nombre.")
            )
            continue
        minutos = _minutos(bloque["inicio"], bloque["fin"])
        if not duracion_valida(minutos):
            plan["errores"].append((
                bloque,
                f"Dura {minutos} minutos: un horario dura como mínimo 1 h 20 min "
                "y crece de a módulos de 40 (80, 120, 160...).",
            ))
            continue
        del_dia = ocupados.setdefault((clave_docente, bloque["dia"]), [])
        if catedra_id is not None and any(
            (i, f, c) == (bloque["inicio"], bloque["fin"], catedra_id)
            for i, f, _, c in del_dia
        ):
            plan["omitidos"].append(bloque)
            continue
        pisado = next(
            (o for o in del_dia if o[0] < bloque["fin"] and bloque["inicio"] < o[1]), None
        )
        if pisado:
            plan["errores"].append((
                bloque,
                f"Se superpone con {pisado[2]} ({pisado[0]:%H:%M} - {pisado[1]:%H:%M}) "
                "del mismo docente.",
            ))
            continue
        del_dia.append((bloque["inicio"], bloque["fin"], bloque["catedra"], catedra_id))
        ids_docente = por_nombre.get(clave_docente)
        plan["horarios"].append(dict(
            bloque,
            carrera_id=ids_carrera.get(clave_carrera),
            catedra_id=catedra_id,
            docente_id=ids_docente[0] if ids_docente else None,
            claves=(clave_carrera, clave_catedra, clave_docente),
        ))

    vistos = set()
    for h in plan["horarios"]:
        clave_carrera, clave_catedra, clave_docente = h["claves"]
        for clave, existe, lista, texto in (
            (clave_carrera, h["carrera_id"], "carreras_nuevas", h["carrera"]),
            (clave_catedra, h["catedra_id"], "catedras_nuevas",
             f"{h['catedra']} ({h['anio']}° año, {h['carrera']})"),
            (clave_docente, h["docente_id"], "docentes_nuevos",
             f"{h['apellido']}, {h['nombre']}"),
        ):
            if existe is None and clave not in vistos:
                vistos.add(clave)
                plan[lista].append(texto)
    return plan


def descripcion_bloque(bloque):
    return (
        f"{NOMBRES_DIAS[bloque['dia']]} {_rango(bloque)}: {bloque['catedra']} - "
        f"{bloque['apellido']}, {bloque['nombre']}"
    )
