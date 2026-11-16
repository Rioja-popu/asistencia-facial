"""Reglas de negocio de la marcación de docentes.

No accede a la base ni a la interfaz: recibe las obligaciones del día ya
consultadas y devuelve qué operación corresponde proponer.

Una obligación es un dict con:
    tipo                 "clase" | "actividad"
    horario_catedra_id   id del horario (clases) o None
    actividad_docente_id id de la participación (actividades) o None
    descripcion          texto para mostrar (cátedra o actividad)
    inicio, fin          datetime.time previstos
    asistencia_id, entrada, salida   None si todavía no hay marcación
"""

from datetime import datetime, timedelta

TOLERANCIA_TARDANZA = timedelta(minutes=5)
# Desde cuánto antes del inicio se puede marcar la entrada
ANTICIPACION_ENTRADA = timedelta(minutes=30)
# Tras marcar la entrada, durante este tiempo no se propone la salida
ESPERA_TRAS_ENTRADA = timedelta(minutes=5)

ENTRADA = "entrada"
SALIDA = "salida"


def _sin_segundos(momento):
    return momento.replace(second=0, microsecond=0)


def es_tardanza(entrada, inicio_previsto):
    """Tardanza: la entrada se registra pasados 5 minutos del inicio previsto."""
    limite = datetime.combine(entrada.date(), inicio_previsto) + TOLERANCIA_TARDANZA
    return _sin_segundos(entrada) > limite


def es_salida_anticipada(salida, fin_previsto):
    return _sin_segundos(salida) < datetime.combine(salida.date(), fin_previsto)


def se_superponen(a, b):
    return a["inicio"] < b["fin"] and b["inicio"] < a["fin"]


def separar_reemplazadas(obligaciones):
    """Si una clase habitual coincide con una actividad especial, manda la actividad.

    Devuelve (vigentes, reemplazadas).
    """
    actividades = [o for o in obligaciones if o["tipo"] == "actividad"]
    vigentes, reemplazadas = [], []
    for obligacion in obligaciones:
        if obligacion["tipo"] == "clase" and any(
            se_superponen(obligacion, actividad) for actividad in actividades
        ):
            reemplazadas.append(obligacion)
        else:
            vigentes.append(obligacion)
    vigentes.sort(key=lambda o: (o["inicio"], o["fin"]))
    return vigentes, reemplazadas


def armar_bloques(obligaciones):
    """Agrupa las obligaciones pegadas (una termina cuando empieza la otra)."""
    bloques = []
    for obligacion in sorted(obligaciones, key=lambda o: (o["inicio"], o["fin"])):
        if bloques and obligacion["inicio"] <= max(o["fin"] for o in bloques[-1]):
            bloques[-1].append(obligacion)
        else:
            bloques.append([obligacion])
    return bloques


def _hora(valor):
    return valor.strftime("%H:%M")


def _rechazo(motivo):
    return {"operacion": None, "motivo": motivo, "items": []}


def proponer_marcacion(obligaciones, ahora):
    """Decide qué registrar para un docente reconocido en el momento `ahora`.

    Devuelve un dict:
        operacion  ENTRADA, SALIDA o None (nada para registrar)
        motivo     explicación cuando operacion es None
        items      obligaciones afectadas, cada una con las claves extra
                   "tardanza" (entradas) o "salida_anticipada" (salidas)
    """
    vigentes, _ = separar_reemplazadas(obligaciones)
    if not vigentes:
        return _rechazo("No tenés actividad programada para hoy.")

    bloques = armar_bloques(vigentes)

    # 1. Primero se cierra lo que está abierto: entrada registrada y sin salida
    for bloque in reversed(bloques):
        abiertas = [o for o in bloque if o["entrada"] and not o["salida"]]
        if not abiertas:
            continue
        ultima_entrada = max(o["entrada"] for o in abiertas)
        if ahora - ultima_entrada < ESPERA_TRAS_ENTRADA:
            return _rechazo(
                f"Entrada ya registrada a las {_hora(ultima_entrada)}. "
                "La salida se puede marcar unos minutos después."
            )
        items = [
            dict(o, salida_anticipada=es_salida_anticipada(ahora, o["fin"]))
            for o in abiertas
        ]
        return {"operacion": SALIDA, "motivo": "", "items": items}

    # 2. Entrada: obligación sin marcar, desde 30 minutos antes del inicio hasta el fin
    hoy = ahora.date()
    for bloque in bloques:
        candidatas = [
            o
            for o in bloque
            if not o["entrada"] and ahora < datetime.combine(hoy, o["fin"])
        ]
        if not candidatas:
            continue
        primera = candidatas[0]
        if ahora < datetime.combine(hoy, primera["inicio"]) - ANTICIPACION_ENTRADA:
            habilitada = datetime.combine(hoy, primera["inicio"]) - ANTICIPACION_ENTRADA
            return _rechazo(
                f"Tu próxima actividad es {primera['descripcion']} a las "
                f"{_hora(primera['inicio'])}. Podés marcar la entrada desde las "
                f"{_hora(habilitada)}."
            )
        items = [dict(o, tardanza=es_tardanza(ahora, o["inicio"])) for o in candidatas]
        return {"operacion": ENTRADA, "motivo": "", "items": items}

    # 3. Nada para registrar
    if all(o["entrada"] and o["salida"] for o in vigentes):
        return _rechazo("Asistencia completa: ya registraste entrada y salida de hoy.")
    return _rechazo(
        "El horario de tus actividades de hoy ya finalizó. "
        "Consultá con el personal administrativo."
    )
