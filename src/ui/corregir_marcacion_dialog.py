from PySide6.QtCore import QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QTimeEdit,
    QVBoxLayout,
)

from services import marcacion_service
from ui import theme


class CorregirMarcacionDialog(QDialog):
    """Carga o corrige a mano la entrada y la salida de una obligación."""

    def __init__(self, docente, fila, parent=None):
        super().__init__(parent)
        self.fila = fila
        self.correccion = None
        self.motivo = ""
        self.setWindowTitle("Corregir marcación")
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        layout.addWidget(theme.etiqueta("Corregir marcación"))
        layout.addWidget(
            theme.etiqueta(
                f"{theme.nombre_docente(docente)} - {theme.fecha(fila['fecha'])}\n"
                f"{fila['descripcion']} ({theme.hora(fila['inicio'])} a "
                f"{theme.hora(fila['fin'])})",
                "subtitulo",
            )
        )

        form = QFormLayout()
        self.time_entrada = QTimeEdit(self._hora(fila["entrada"], fila["inicio"]))
        self.chk_salida = QCheckBox("Registrar salida")
        self.chk_salida.setChecked(True)
        self.time_salida = QTimeEdit(self._hora(fila["salida"], fila["fin"]))
        for campo in (self.time_entrada, self.time_salida):
            campo.setDisplayFormat("HH:mm")
        self.chk_salida.toggled.connect(self.time_salida.setEnabled)
        self.input_motivo = QLineEdit()
        self.input_motivo.setMaxLength(255)
        self.input_motivo.setPlaceholderText("Ej.: se olvidó de marcar la salida")
        form.addRow("Entrada:", self.time_entrada)
        form.addRow("", self.chk_salida)
        form.addRow("Salida:", self.time_salida)
        form.addRow("Motivo:", self.input_motivo)
        layout.addLayout(form)
        layout.addWidget(
            theme.etiqueta(
                "La tardanza y la salida anticipada se recalculan con las horas cargadas. "
                "Queda registrado quién hizo la corrección y cuándo.",
                "subtitulo",
            )
        )

        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(theme.boton("Guardar", "confirmar", self._guardar))
        botones.addWidget(theme.boton("Cancelar", "peligro", self.reject))
        layout.addLayout(botones)

    @staticmethod
    def _hora(marcada, prevista):
        valor = marcada.time() if marcada else prevista
        return QTime(valor.hour, valor.minute)

    def _guardar(self):
        motivo = self.input_motivo.text().strip()
        if not motivo:
            theme.avisar(self, "Dato faltante", "Escribí el motivo de la corrección.")
            return
        salida = self.time_salida.time().toPython() if self.chk_salida.isChecked() else None
        try:
            self.correccion = marcacion_service.preparar_correccion(
                self.fila["fecha"], self.fila["inicio"], self.fila["fin"],
                self.time_entrada.time().toPython(), salida,
            )
        except ValueError as e:
            theme.avisar(self, "Horas inválidas", str(e))
            return
        self.motivo = motivo
        self.accept()
