from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from repositories import (
    asistencia_repository,
    ausencia_repository,
    docente_repository,
    no_laborable_repository,
)
from services import situacion_service
from ui import theme

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# (clave de situacion_service.resumen_del_dia, título, color)
TARJETAS = [
    ("con_obligaciones", "Docentes con actividad hoy", theme.AZUL),
    ("marcaron", "Ya marcaron", theme.VERDE),
    ("por_llegar", "Todavía no les toca", theme.GRIS),
    ("con_aviso", "Ausentes con aviso", theme.AZUL_CLARO),
    ("sin_aviso", "Ausentes sin aviso", theme.ROJO),
]


def fecha_larga(fecha):
    dia = theme.DIAS_SEMANA[fecha.isoweekday()]
    return f"{dia} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


class InicioView(QWidget):
    """Resumen del día: cuántos docentes tienen actividad, quién marcó y quién falta."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)

        encabezado = QHBoxLayout()
        titulos = QVBoxLayout()
        titulos.addWidget(theme.etiqueta("Resumen del día"))
        self.lbl_fecha = theme.etiqueta("", "subtitulo")
        titulos.addWidget(self.lbl_fecha)
        encabezado.addLayout(titulos, 1)
        encabezado.addWidget(
            theme.boton("Actualizar", "secundario", self.refrescar),
            alignment=Qt.AlignmentFlag.AlignBottom,
        )
        layout.addLayout(encabezado)

        self.lbl_no_laborable = QLabel()
        self.lbl_no_laborable.setWordWrap(True)
        fondo, texto = theme.COLORES_ESTADO["atencion"]
        self.lbl_no_laborable.setStyleSheet(
            f"background-color: {fondo}; color: {texto}; font-weight: bold;"
            "padding: 8px 12px; border-radius: 6px;"
        )
        self.lbl_no_laborable.hide()
        layout.addWidget(self.lbl_no_laborable)

        fila = QHBoxLayout()
        fila.setSpacing(12)
        self.numeros = {}
        for clave, titulo, color in TARJETAS:
            tarjeta = QFrame()
            tarjeta.setObjectName("tarjeta")
            tarjeta.setStyleSheet(f"QFrame#tarjeta {{ border-top: 4px solid {color}; }}")
            interior = QVBoxLayout(tarjeta)
            interior.setContentsMargins(14, 10, 14, 12)
            numero = QLabel("0")
            numero.setStyleSheet(f"font-size: 30px; font-weight: bold; color: {color};")
            interior.addWidget(numero)
            interior.addWidget(theme.etiqueta(titulo, "subtitulo"))
            self.numeros[clave] = numero
            fila.addWidget(tarjeta, 1)
        layout.addSpacing(6)
        layout.addLayout(fila)

        layout.addSpacing(10)
        layout.addWidget(theme.etiqueta("Actividad de hoy", "seccion"))
        self.tabla = theme.crear_tabla(
            ["Docente", "Obligación", "Horario", "Entrada", "Salida", "Situación"],
            "Hoy ningún docente tiene clases ni actividades.",
        )
        layout.addWidget(self.tabla, 1)

    def refrescar(self):
        ahora = datetime.now()
        hoy = ahora.date()
        self.lbl_fecha.setText(f"{fecha_larga(hoy)}, {ahora:%H:%M} h")
        try:
            no_laborables = no_laborable_repository.del_dia(hoy)
            por_docente = []
            for docente in docente_repository.listar_docentes(solo_activos=True):
                filas = situacion_service.clasificar(
                    asistencia_repository.obtener_obligaciones(docente["id"], hoy),
                    ausencia_repository.obtener_ausencias(docente["id"], hoy, hoy),
                    ahora,
                )
                if filas:
                    por_docente.append((theme.nombre_docente(docente), filas))
        except Exception as e:
            theme.error_bd(self, e)
            return

        if no_laborables:
            self.lbl_no_laborable.setText(
                "Hoy no hay clases. " + ". ".join(no_laborables)
                + ". Sólo cuentan las mesas y jornadas cargadas para hoy."
            )
        self.lbl_no_laborable.setVisible(bool(no_laborables))

        resumen = situacion_service.resumen_del_dia([filas for _, filas in por_docente])
        for clave, numero in self.numeros.items():
            numero.setText(str(resumen[clave]))

        detalle = sorted(
            ((nombre, f) for nombre, filas in por_docente for f in filas),
            key=lambda par: (par[1]["inicio"], par[1]["fin"], par[0]),
        )
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    nombre, f["descripcion"],
                    f"{theme.hora(f['inicio'])} - {theme.hora(f['fin'])}",
                    theme.hora(f["entrada"]), theme.hora(f["salida"]), f["situacion"],
                ]
                for nombre, f in detalle
            ],
            estados={
                (i, 5): situacion_service.gravedad(f["etiquetas"])
                for i, (_, f) in enumerate(detalle)
            },
        )
