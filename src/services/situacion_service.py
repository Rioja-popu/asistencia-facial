"""Clasifica cada obligación de un docente para la consulta y los informes.

Trabaja sobre datos ya consultados; no accede a la base.
"""

from datetime import datetime

from services.marcacion_service import separar_reemplazadas

EN_HORARIO = "En horario"
TARDANZA = "Tardanza"
SALIDA_ANTICIPADA = "Salida anticipada"
SALIDA_SIN_REGISTRAR = "Salida sin registrar"
EN_CURSO = "En curso"
AUSENTE_CON_AVISO = "Ausente con aviso"
AUSENTE_SIN_AVISO = "Ausente sin aviso"
AUSENCIA_NO_JUSTIFICADA = "Ausencia médica no justificada"
REEMPLAZADA = "Reemplazada por actividad especial"
PROGRAMADA = "Programada"

DETALLE_AUSENCIA = {
    ("particular", "registrada"): "particular",
    ("medica", "pendiente_certificado"): "médica, certificado pendiente",
    ("medica", "justificada"): "médica justificada",
}

# Orden en el que se muestran los totales del informe
ORDEN_TOTALES = [
    EN_HORARIO,
    TARDANZA,
    SALIDA_ANTICIPADA,
    SALIDA_SIN_REGISTRAR,
    AUSENTE_CON_AVISO,
    AUSENTE_SIN_AVISO,
    AUSENCIA_NO_JUSTIFICADA,
    REEMPLAZADA,
]


def _situacion_ausente(ausencia, obligacion, ahora):
    if ausencia:
        clave = (ausencia["tipo"], ausencia["estado"])
        if clave in DETALLE_AUSENCIA:
            return [AUSENTE_CON_AVISO], f"{AUSENTE_CON_AVISO} ({DETALLE_AUSENCIA[clave]})"
        return [AUSENCIA_NO_JUSTIFICADA], AUSENCIA_NO_JUSTIFICADA
    if datetime.combine(obligacion["fecha"], obligacion["fin"]) <= ahora:
        return [AUSENTE_SIN_AVISO], AUSENTE_SIN_AVISO
    return [], PROGRAMADA


def _situacion_presente(ausencia, obligacion, ahora):
    etiquetas = [TARDANZA if obligacion["tardanza"] else EN_HORARIO]
    if obligacion["salida"]:
        if obligacion["salida_anticipada"]:
            etiquetas.append(SALIDA_ANTICIPADA)
    elif datetime.combine(obligacion["fecha"], obligacion["fin"]) <= ahora:
        etiquetas.append(SALIDA_SIN_REGISTRAR)
    else:
        etiquetas.append(EN_CURSO)
    texto = ", ".join(etiquetas)
    if ausencia:
        texto += " (tenía una ausencia cargada: revisar)"
    return [e for e in etiquetas if e != EN_CURSO], texto


def clasificar(obligaciones, ausencias, ahora):
    """Devuelve una fila por obligación con su situación.

    obligaciones: salida de asistencia_repository.obtener_obligaciones
    ausencias:    {fecha: {"tipo", "estado"}}
    Cada fila: fecha, descripcion, inicio, fin, entrada, salida, situacion, etiquetas
    """
    filas = []
    fechas = sorted({o["fecha"] for o in obligaciones})
    for fecha in fechas:
        del_dia = [o for o in obligaciones if o["fecha"] == fecha]
        vigentes, reemplazadas = separar_reemplazadas(del_dia)
        ausencia = ausencias.get(fecha)
        for obligacion in sorted(del_dia, key=lambda o: (o["inicio"], o["fin"])):
            if obligacion in reemplazadas and not obligacion["entrada"]:
                etiquetas, texto = [REEMPLAZADA], REEMPLAZADA
            elif obligacion["entrada"]:
                etiquetas, texto = _situacion_presente(ausencia, obligacion, ahora)
            else:
                etiquetas, texto = _situacion_ausente(ausencia, obligacion, ahora)
            filas.append(
                {
                    "fecha": fecha,
                    "descripcion": obligacion["descripcion"],
                    "inicio": obligacion["inicio"],
                    "fin": obligacion["fin"],
                    "entrada": obligacion["entrada"],
                    "salida": obligacion["salida"],
                    "situacion": texto,
                    "etiquetas": etiquetas,
                }
            )
    return filas


def totales(filas):
    """[(situación, cantidad), ...] sólo con las situaciones que aparecen."""
    conteo = {}
    for fila in filas:
        for etiqueta in fila["etiquetas"]:
            conteo[etiqueta] = conteo.get(etiqueta, 0) + 1
    return [(nombre, conteo[nombre]) for nombre in ORDEN_TOTALES if nombre in conteo]
