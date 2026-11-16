from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from repositories import no_laborable_repository as repo
from ui import theme

TIPOS = {"feriado": "Feriado", "receso": "Receso"}


class NoLaborablesView(QWidget):
    """Feriados y recesos: esos días las clases habituales no cuentan como ausencia."""

    def __init__(self):
        super().__init__()
        self.registros = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Feriados y recesos"))
        layout.addWidget(
            theme.etiqueta(
                "En estos días las clases habituales no se dictan: no se pide marcación y "
                "no figuran como ausencia. Las mesas y jornadas cargadas en Actividades "
                "especiales se mantienen.",
                "subtitulo",
            )
        )

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        form = QFormLayout(tarjeta)
        self.combo_tipo = theme.combo([(nombre, tipo) for tipo, nombre in TIPOS.items()])
        self.combo_tipo.currentIndexChanged.connect(self._ajustar_fechas)
        self.input_descripcion = QLineEdit()
        self.input_descripcion.setMaxLength(255)
        self.input_descripcion.setPlaceholderText("Ej.: Día de la Soberanía Nacional")
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_hasta = QDateEdit(QDate.currentDate())
        for campo in (self.date_desde, self.date_hasta):
            campo.setDisplayFormat("dd/MM/yyyy")
            campo.setCalendarPopup(True)
        self.date_desde.dateChanged.connect(self._ajustar_fechas)
        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Descripción:", self.input_descripcion)
        form.addRow("Desde:", self.date_desde)
        form.addRow("Hasta:", self.date_hasta)
        layout.addWidget(tarjeta)
        layout.addWidget(theme.boton("Agregar", "confirmar", self._agregar))

        self.tabla = theme.crear_tabla(
            ["Tipo", "Descripción", "Desde", "Hasta", "Días"],
            "Todavía no hay feriados ni recesos cargados.",
        )
        layout.addWidget(self.tabla)

        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Eliminar", "peligro", self._eliminar))
        fila.addStretch()
        layout.addLayout(fila)
        self._ajustar_fechas()

    def _ajustar_fechas(self):
        """Un feriado dura un día; un receso va de una fecha a otra."""
        es_feriado = self.combo_tipo.currentData() == "feriado"
        self.date_hasta.setEnabled(not es_feriado)
        if es_feriado or self.date_hasta.date() < self.date_desde.date():
            self.date_hasta.setDate(self.date_desde.date())

    def refrescar(self):
        try:
            registros = repo.listar()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.registros = {r["id"]: r for r in registros}
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    TIPOS[r["tipo"]],
                    r["descripcion"],
                    theme.fecha(r["fecha_desde"]),
                    theme.fecha(r["fecha_hasta"]),
                    (r["fecha_hasta"] - r["fecha_desde"]).days + 1,
                ]
                for r in registros
            ],
            [r["id"] for r in registros],
        )

    def _agregar(self):
        descripcion = self.input_descripcion.text().strip()
        if not descripcion:
            theme.avisar(self, "Dato faltante", "Escribí una descripción.")
            return
        desde = self.date_desde.date().toPython()
        hasta = self.date_hasta.date().toPython()
        if hasta < desde:
            theme.avisar(self, "Período inválido", "La fecha 'hasta' es anterior a 'desde'.")
            return
        try:
            repo.registrar(self.combo_tipo.currentData(), descripcion, desde, hasta)
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.input_descripcion.clear()
        self.refrescar()

    def _eliminar(self):
        registro_id = theme.id_seleccionado(self.tabla)
        if registro_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná un feriado o receso de la lista.")
            return
        registro = self.registros[registro_id]
        if not theme.confirmar(
            self, "Eliminar",
            f"¿Eliminar \"{registro['descripcion']}\"? Las clases de esos días "
            "vuelven a contar como obligaciones.",
        ):
            return
        try:
            repo.eliminar(registro_id)
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar()
