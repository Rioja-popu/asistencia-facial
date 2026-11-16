"""Importación de docentes desde un listado en Excel o CSV.

La primera fila con "Apellido" y "Nombre" es el encabezado; debajo va un
docente por fila. No accede a la base: `leer_listado` devuelve las filas leídas
y `planificar` decide qué se crea y qué se completa con los docentes ya cargados.
"""

import csv
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from services.importacion_service import _limpio, _nombre_propio, normalizar

COLUMNAS = [
    ("apellido", "APELLIDO"),
    ("nombre", "NOMBRE"),
    ("dni", "DNI"),
    ("cuil", "CUIL"),
    ("celular", "CELULAR"),
    ("correo_electronico", "CORREO ELECTRONICO"),
]
# Otras formas de escribir cada encabezado, ya normalizadas
ALIAS = {
    "apellido": "apellido", "apellidos": "apellido",
    "nombre": "nombre", "nombres": "nombre",
    "dni": "dni", "documento": "dni",
    "cuil": "cuil", "cuit": "cuil",
    "celular": "celular", "telefono": "celular",
    "correo electronico": "correo_electronico", "correo": "correo_electronico",
    "email": "correo_electronico", "e-mail": "correo_electronico",
    "mail": "correo_electronico",
}
COMPLETABLES = [
    ("dni", "DNI"), ("cuil", "CUIL"),
    ("celular", "celular"), ("correo_electronico", "correo"),
]
HOJA_INSTRUCCIONES = "Instrucciones"
INSTRUCCIONES = [
    "Cómo completar el listado",
    "1. Un docente por fila. Apellido, nombre y DNI son obligatorios.",
    "2. DNI: 7 u 8 números. CUIL: 11 números. Los puntos y guiones se ignoran.",
    "3. Celular (sólo números) y correo electrónico son opcionales.",
    "4. Si el docente ya existe (mismo DNI, o mismo apellido y nombre sin DNI cargado) "
    "no se duplica: sólo se completan los datos que le falten.",
    "5. Escribí apellido y nombre igual que en la planilla de horarios.",
    "6. Las fotos no se importan: se toman después en la pantalla Docentes.",
    "7. Esta hoja de instrucciones no se importa.",
]
_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _numero(valor):
    """Texto de una celda numérica: Excel puede traer 28456123 como 28456123.0."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return re.sub(r"[\s.\-+()]", "", _limpio(valor))


def generar_planilla(ruta, docentes=()):
    """Listado modelo; `docentes` son filas de ejemplo en el orden de COLUMNAS."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Docentes"
    for columna, (_, titulo) in enumerate(COLUMNAS, start=1):
        celda = hoja.cell(row=1, column=columna, value=titulo)
        celda.font = Font(bold=True)
        celda.fill = PatternFill("solid", start_color="D9D9D9")
        celda.alignment = Alignment(horizontal="center")
    for fila, docente in enumerate(docentes, start=2):
        for columna, valor in enumerate(docente, start=1):
            celda = hoja.cell(row=fila, column=columna, value=valor)
            celda.number_format = "@"  # Como texto, para que Excel no altere DNI ni CUIL
    for letra, ancho in zip("ABCDEF", (22, 26, 14, 16, 16, 36)):
        hoja.column_dimensions[letra].width = ancho
    ayuda = libro.create_sheet(HOJA_INSTRUCCIONES)
    ayuda.column_dimensions["A"].width = 110
    for i, texto in enumerate(INSTRUCCIONES, start=1):
        celda = ayuda.cell(row=i, column=1, value=texto)
        celda.alignment = Alignment(wrap_text=True, vertical="top")
        if i == 1:
            celda.font = Font(bold=True, size=13)
    libro.save(ruta)


# ---------- Lectura ----------

def _filas_csv(ruta):
    with open(ruta, "rb") as archivo:
        crudo = archivo.read()
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = crudo.decode("latin-1")  # CSV guardado desde Excel en Windows
    primera = texto.splitlines()[0] if texto.strip() else ""
    separador = ";" if primera.count(";") > primera.count(",") else ","
    return list(csv.reader(texto.splitlines(), delimiter=separador))


def _filas_excel(ruta):
    libro = load_workbook(ruta, data_only=True)
    hojas = [h for h in libro.worksheets if h.title != HOJA_INSTRUCCIONES]
    return [list(fila) for fila in hojas[0].iter_rows(values_only=True)] if hojas else []


def leer_listado(ruta):
    """Devuelve (docentes, errores). Cada docente lleva el número de fila del archivo."""
    filas = _filas_csv(ruta) if ruta.lower().endswith(".csv") else _filas_excel(ruta)
    columnas, inicio = None, 0
    for i, fila in enumerate(filas):
        encontradas = {}
        for j, valor in enumerate(fila):
            campo = ALIAS.get(normalizar(_limpio(valor)))
            if campo:
                encontradas.setdefault(campo, j)
        if "apellido" in encontradas and "nombre" in encontradas:
            columnas, inicio = encontradas, i + 1
            break
    if columnas is None:
        return [], ["No se encontró el encabezado: tiene que haber columnas APELLIDO y NOMBRE."]

    docentes = []
    for numero, fila in enumerate(filas[inicio:], start=inicio + 1):
        def celda(campo):
            j = columnas.get(campo)
            return fila[j] if j is not None and j < len(fila) else None

        docente = {
            "fila": numero,
            "apellido": _nombre_propio(_limpio(celda("apellido"))),
            "nombre": _nombre_propio(_limpio(celda("nombre"))),
            "dni": _numero(celda("dni")),
            "cuil": _numero(celda("cuil")),
            "celular": _numero(celda("celular")),
            "correo_electronico": _limpio(celda("correo_electronico")),
        }
        if any(v for k, v in docente.items() if k != "fila"):
            docentes.append(docente)
    return docentes, []


# ---------- Plan de importación ----------

def _clave(docente):
    return (normalizar(docente["apellido"]), normalizar(docente["nombre"]))


def _error_de_datos(d):
    if not d["apellido"] or not d["nombre"]:
        return "falta el apellido o el nombre"
    if not d["dni"]:
        return "falta el DNI"
    if not (d["dni"].isdigit() and len(d["dni"]) in (7, 8)):
        return "el DNI tiene que tener 7 u 8 números"
    if d["cuil"] and not (d["cuil"].isdigit() and len(d["cuil"]) == 11):
        return "el CUIL tiene que tener 11 números"
    if d["celular"] and not d["celular"].isdigit():
        return "el celular sólo lleva números"
    if d["correo_electronico"] and not _CORREO.match(d["correo_electronico"]):
        return "el correo electrónico no es válido"
    return None


def _parecido(docente, existentes):
    """Docente ya cargado con el mismo apellido y un nombre que empieza igual."""
    apellido, nombre = _clave(docente)
    for e in existentes:
        otro_apellido, otro_nombre = _clave(e)
        if otro_apellido == apellido and otro_nombre != nombre and (
            (nombre + " ").startswith(otro_nombre + " ")
            or (otro_nombre + " ").startswith(nombre + " ")
        ):
            return e
    return None


def planificar(docentes, existentes):
    """Decide qué pasa con cada fila del listado.

    Devuelve un dict con:
      nuevos       docentes a crear (con "aviso" si se parecen a uno ya cargado)
      completados  [(docente, id del existente, {campo: valor})]: datos que le faltaban
      sin_cambios  docentes que ya estaban cargados con todos esos datos
      errores      [(docente, motivo)]
    Nunca se pisa un dato ya cargado: sólo se completan los vacíos.
    """
    plan = {"nuevos": [], "completados": [], "sin_cambios": [], "errores": []}
    por_dni = {e["dni"]: e for e in existentes if e["dni"]}
    por_cuil = {e["cuil"]: e for e in existentes if e["cuil"]}
    por_nombre = {}
    for e in existentes:
        por_nombre.setdefault(_clave(e), []).append(e)
    dnis, cuiles, nombres, usados = set(), set(), set(), set()

    for d in docentes:
        error = _error_de_datos(d)
        if not error and d["dni"] in dnis:
            error = "el DNI está repetido en el listado"
        if not error and d["cuil"] and d["cuil"] in cuiles:
            error = "el CUIL está repetido en el listado"
        if not error and _clave(d) in nombres:
            error = "el apellido y nombre están repetidos en el listado"
        existente = None
        if not error:
            existente = por_dni.get(d["dni"])
            if existente is None:
                homonimos = por_nombre.get(_clave(d), [])
                sin_dni = [e for e in homonimos if not e["dni"]]
                if len(sin_dni) == 1:
                    existente = sin_dni[0]
                elif homonimos:
                    error = (
                        "ya hay un docente con ese apellido y nombre y otro DNI"
                        if not sin_dni else
                        "hay más de un docente con ese apellido y nombre"
                    )
        if not error and d["cuil"]:
            dueno = por_cuil.get(d["cuil"])
            if dueno and (existente is None or dueno["id"] != existente["id"]):
                error = "el CUIL ya pertenece a otro docente"
        if not error and existente and existente["id"] in usados:
            error = "coincide con el mismo docente que otra fila del listado"
        if error:
            plan["errores"].append((d, error))
            continue

        dnis.add(d["dni"])
        nombres.add(_clave(d))
        if d["cuil"]:
            cuiles.add(d["cuil"])
        if existente is None:
            parecido = _parecido(d, existentes)
            plan["nuevos"].append(dict(
                d,
                aviso=f"revisar: se parece a {parecido['apellido']}, {parecido['nombre']}"
                if parecido else None,
            ))
            continue
        usados.add(existente["id"])
        faltantes = {
            campo: d[campo] for campo, _ in COMPLETABLES
            if d[campo] and not existente[campo]
        }
        if faltantes:
            plan["completados"].append((d, existente["id"], faltantes))
        else:
            plan["sin_cambios"].append(d)
    return plan


def descripcion_faltantes(faltantes):
    return ", ".join(titulo for campo, titulo in COMPLETABLES if campo in faltantes)
