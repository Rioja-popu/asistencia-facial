from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from services.camera_service import CameraWorker
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AttendanceView(QWidget):

    def __init__(self, jornada_view):
        super().__init__()
        self.jornada_view = jornada_view
        self.camera_open = False
        self.camera_worker = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Título del módulo
        title_label = QLabel("📷 Asistencia por Captura Facial")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;"
        )
        main_layout.addWidget(title_label)

        # -------------------------------------------------------------
        # BOTONES ABRIR / CERRAR CÁMARA
        # -------------------------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_abrir = QPushButton("Abrir Cámara")
        self.btn_cerrar = QPushButton("Cerrar Cámara")

        # Aplicar estilos visuales
        self._aplicar_estilos_botones()

        btn_layout.addWidget(self.btn_abrir)
        btn_layout.addWidget(self.btn_cerrar)
        btn_layout.addStretch()

        main_layout.addLayout(btn_layout)

        # -------------------------------------------------------------
        # PANEL DE VIDEO (VACÍO POR AHORA)
        # -------------------------------------------------------------
        self.video_panel = QLabel("Apagado y Próximo")
        self.video_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_panel.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                color: #a0a0a0;
                font-size: 16px;
                font-weight: bold;
                margin-top: 15px;
            }
        """
        )
        self.video_panel.setMinimumHeight(400)
        main_layout.addWidget(self.video_panel)

        # Eventos de los botones de la cámara
        self.btn_abrir.clicked.connect(self._abrir_camara)
        self.btn_cerrar.clicked.connect(self._cerrar_camara)

        # -------------------------------------------------------------
        # CONEXIÓN Y EVALUACIÓN DE ESTADO (AL FINAL DEL INIT)
        # -------------------------------------------------------------
        self.jornada_view.time_entrada.timeChanged.connect(
            self.evaluar_estado_botones
        )
        self.jornada_view.time_salida.timeChanged.connect(
            self.evaluar_estado_botones
        )
        self.jornada_view.input_catedra.textChanged.connect(
            self.evaluar_estado_botones
        )

        # Evaluar el estado inicial una vez creados los botones
        self.evaluar_estado_botones()

    def _aplicar_estilos_botones(self):
        self.btn_abrir.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #219150; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """
        )

        self.btn_cerrar.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """
        )

    def evaluar_estado_botones(self):
        """Reevalúa la configuración de la jornada e inactiva la cámara si faltan datos."""
        jornada_lista = self._jornada_esta_configurada()

        if not jornada_lista:
            # Si la jornada ya no está lista, forzar el cierre inmediato de la cámara
            if self.camera_open:
                self._cerrar_camara()
            self.camera_open = False
            self.btn_abrir.setEnabled(False)
            self.btn_cerrar.setEnabled(False)
        else:
            # Si la jornada está completa y la cámara no está abierta, habilitar 'Abrir'
            if not self.camera_open:
                self.btn_abrir.setEnabled(True)
                self.btn_cerrar.setEnabled(False)

    def _jornada_esta_configurada(self):
        text_entrada = self.jornada_view.time_entrada.text()
        text_salida = self.jornada_view.time_salida.text()
        text_catedra = self.jornada_view.input_catedra.text().strip()

        # Verifica que los horarios no sean '--:--' y que la cátedra no esté vacía
        return (
            text_entrada != "--:--"
            and text_salida != "--:--"
            and text_catedra != ""
        )

    def _abrir_camara(self):
            self.camera_open = True
            self.btn_abrir.setEnabled(False)
            self.btn_cerrar.setEnabled(True)
    
            # Iniciar el hilo de captura de la webcam
            self.camera_worker = CameraWorker()
            self.camera_worker.frame_received.connect(self._actualizar_frame_panel)
            self.camera_worker.start()

    def _cerrar_camara(self):
        self.camera_open = False

        # Detener la cámara y liberar el recurso
        if self.camera_worker and self.camera_worker.isRunning():
            self.camera_worker.stop()
            self.camera_worker = None

        # Limpiar el panel y restaurar el texto inicial
        self.video_panel.clear()
        self.video_panel.setText("Apagado y Próximo")

        self.evaluar_estado_botones()

    def _actualizar_frame_panel(self, q_image, raw_frame):
        if self.camera_open:
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                self.video_panel.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.video_panel.setPixmap(scaled_pixmap)