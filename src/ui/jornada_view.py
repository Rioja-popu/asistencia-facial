from database.queries import crear_jornada, actualizar_jornada
from datetime import datetime
from PySide6.QtCore import QTime, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
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

    def __init__(self, usuario_id):
        super().__init__()
        self.usuario_id = usuario_id
        self.jornada_id = None
        self.modo_edicion = False

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
                border: none;
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
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
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

        # Botones
        self.btn_guardar = QPushButton("Guardar Jornada")
        self.btn_editar = QPushButton("Editar Jornada")
        self.btn_terminar = QPushButton("Terminar Jornada")

        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.btn_terminar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)

        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(0, 10, 0, 0)
        btn_box.addWidget(self.btn_guardar)
        btn_box.addWidget(self.btn_editar)
        btn_box.addWidget(self.btn_terminar)

        form_layout.addRow("", btn_box)

        # Agregar el frame único con el formulario al layout principal
        main_layout.addWidget(form_frame)

        # Conexiones de los botones
        self.btn_guardar.clicked.connect(self._guardar_jornada)
        self.btn_editar.clicked.connect(self._editar_jornada)
        self.btn_terminar.clicked.connect(self._terminar_jornada)

    def _guardar_jornada(self):
    # 1. Obtener la fecha en formato YYYY-MM-DD para PostgreSQL
        texto_fecha = self.lbl_fecha.text()
        fecha = datetime.strptime(texto_fecha, "%d/%m/%Y").strftime("%Y-%m-%d")

    # 2. Obtener horarios (usar "hh:mm:ss" en minúscula para QTime)
        h_entrada = self.time_entrada.time().toString("hh:mm:ss")
        h_salida = self.time_salida.time().toString("hh:mm:ss")
        catedra = self.input_catedra.text().strip()

        if not catedra:
            QMessageBox.warning(
                self, "Atención", "Ingrese el nombre de la Cátedra."
            )
            return

        try:
            if not self.modo_edicion:
                self.jornada_id = crear_jornada(
                    fecha, h_entrada, h_salida, catedra, self.usuario_id
                )
            else:
            # UPDATE de la jornada existente
                actualizar_jornada(
                    self.jornada_id, fecha, h_entrada, h_salida, catedra
                )
                self.modo_edicion = False

            self._bloquear_controles(True)
            self.btn_guardar.hide()
            self.btn_editar.show()
            self.btn_terminar.show()

        except Exception as e:
            QMessageBox.critical(
                self, "Error de base de datos", f"No se pudo guardar la jornada: {e}"
            )

    def _editar_jornada(self):
        self.modo_edicion = True
        self._bloquear_controles(False)
        self.btn_guardar.show()
        self.btn_editar.hide()

    def _terminar_jornada(self):
        self.jornada_id = None
        self.modo_edicion = False
        self._bloquear_controles(False)

        # Resetear valores iniciales
        self.input_catedra.clear()
        # Actualizar el texto del QLabel con la fecha actual
        self.lbl_fecha.setText(datetime.now().strftime("%d/%m/%Y"))
        self.btn_guardar.show()
        self.btn_editar.hide()
        self.btn_terminar.hide()

    def _bloquear_controles(self, bloquear: bool):
        self.time_entrada.setEnabled(not bloquear)
        self.time_salida.setEnabled(not bloquear)
        self.input_catedra.setEnabled(not bloquear)

    def esta_lista_y_guardada(self):
        return self.jornada_id is not None and not self.modo_edicion

