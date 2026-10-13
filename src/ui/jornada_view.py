from datetime import datetime
from PySide6.QtCore import QTime, Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


class CustomTimeEdit(QTimeEdit):
    """QTimeEdit personalizado que muestra '--:--' cuando no se configuró una hora."""

    def __init__(self, parent=None):
        self.special_text = "--:--"  # Define la variable ANTES de inicializar el padre
        super().__init__(parent)
        self.setDisplayFormat("hh:mm")
        self.clear()

    def set_unconfigured(self):
        self.special_text = "--:--"
        self.clear()

    def textFromDateTime(self, dt):
        # Utiliza getattr para verificar con seguridad sin lanzar AttributeError
        if getattr(self, "special_text", None):
            return self.special_text
        return super().textFromDateTime(dt)

    def stepBy(self, steps):
        if getattr(self, "special_text", None):
            self.special_text = None
            self.setTime(QTime(8, 0))
        else:
            super().stepBy(steps)

    def focusInEvent(self, event):
        if getattr(self, "special_text", None):
            self.special_text = None
            self.setTime(QTime(8, 0))
        super().focusInEvent(event)


class JornadaView(QWidget):

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(40, 30, 40, 30)

        # Título del módulo
        title_label = QLabel("⚙️ Configuración de la Jornada")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;"
        )
        main_layout.addWidget(title_label)

        # Contenedor del formulario
        form_frame = QFrame()
        form_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #34495e;
            }
            QLineEdit, QTimeEdit {
                font-size: 14px;
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                min-width: 180px;
                color: #2c3e50;               
                background-color: #ffffff;
            }
        """
        )

        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)

        # 1. Fecha del Sistema
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        self.lbl_fecha = QLabel(fecha_actual)
        self.lbl_fecha.setStyleSheet(
            "font-size: 14px; font-weight: normal; color: #2c3e50;"
        )
        form_layout.addRow("Fecha:", self.lbl_fecha)

        # 2. Horario de entrada (--:--)
        self.time_entrada = CustomTimeEdit()
        form_layout.addRow("Horario de entrada:", self.time_entrada)

        # 3. Horario de salida (--:--)
        self.time_salida = CustomTimeEdit()
        form_layout.addRow("Horario de salida:", self.time_salida)

        # 4. Cátedra (String vacío)
        self.input_catedra = QLineEdit()
        self.input_catedra.setPlaceholderText("Ingrese la cátedra")
        form_layout.addRow("Cátedra:", self.input_catedra)

        main_layout.addWidget(form_frame)