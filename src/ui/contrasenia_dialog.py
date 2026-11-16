from PySide6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLineEdit, QVBoxLayout

from services import usuario_service
from ui import theme


def campo_contrasenia():
    campo = QLineEdit()
    campo.setEchoMode(QLineEdit.EchoMode.Password)
    campo.setMaxLength(128)
    return campo


class ContraseniaDialog(QDialog):
    """Pide una contraseña nueva (dos veces) y, si es la propia, también la actual."""

    def __init__(self, titulo, detalle, contrasenia_guardada=None, parent=None):
        super().__init__(parent)
        self.contrasenia_guardada = contrasenia_guardada
        self.nueva = None
        self.setWindowTitle(titulo)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.addWidget(theme.etiqueta(titulo))
        layout.addWidget(theme.etiqueta(detalle, "subtitulo"))

        form = QFormLayout()
        self.input_actual = campo_contrasenia()
        self.input_nueva = campo_contrasenia()
        self.input_repetida = campo_contrasenia()
        if contrasenia_guardada is not None:
            form.addRow("Contraseña actual:", self.input_actual)
        form.addRow("Contraseña nueva:", self.input_nueva)
        form.addRow("Repetir la nueva:", self.input_repetida)
        layout.addLayout(form)

        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(theme.boton("Guardar", "confirmar", self._guardar))
        botones.addWidget(theme.boton("Cancelar", "neutro", self.reject))
        layout.addLayout(botones)

    def _guardar(self):
        if self.contrasenia_guardada is not None and not usuario_service.coincide(
            self.input_actual.text(), self.contrasenia_guardada
        ):
            theme.avisar(self, "Contraseña incorrecta", "La contraseña actual no es correcta.")
            return
        try:
            usuario_service.validar_contrasenia(
                self.input_nueva.text(), self.input_repetida.text()
            )
        except ValueError as e:
            theme.avisar(self, "Contraseña inválida", str(e))
            return
        self.nueva = usuario_service.cifrar(self.input_nueva.text())
        self.accept()
