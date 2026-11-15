import time
from datetime import datetime, timedelta
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QPixmap
from services.camera_service import CameraWorker
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from database.queries import (
    obtener_alumnos_con_fotos,
    obtener_asistencia_alumno,
    registrar_entrada_asistencia,
    registrar_salida_asistencia,
)
from services.camera_service import CameraWorker
from services.facial_service import FacialRecognitionService

class AttendanceView(QWidget):

    def __init__(self, jornada_view):
        super().__init__()
        self.jornada_view = jornada_view
        self.camera_open = False
        self.camera_worker = None

        # Inicializar el servicio de reconocimiento facial
        self.facial_service = FacialRecognitionService()

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

        # Mensaje superpuesto en la esquina inferior izquierda del panel de video
        self.lbl_overlay = QLabel(self.video_panel)
        self.lbl_overlay.setStyleSheet(
            """
            QLabel {
                border: none;
                border-radius: 4px;
                background-color: rgba(0, 0, 0, 170);
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                margin: 0px;
                padding: 4px 10px;
            }
        """
        )
        self.lbl_overlay.hide()
        self.video_panel.installEventFilter(self)

        # Vuelve a "Escaneando..." unos segundos después de marcar entrada o salida
        self.overlay_timer = QTimer(self)
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.setInterval(3000)
        self.overlay_timer.timeout.connect(
            lambda: self._mostrar_overlay("Escaneando...")
        )

        self.lbl_estado = QLabel("Cámara cerrada.")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;"
        )

        main_layout.addWidget(self.video_panel)
        main_layout.addWidget(self.lbl_estado)

        # Mientras no pase este instante, el resultado de un registro queda en pantalla
        self._estado_fijo_hasta = 0.0

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
            # Impedir abrir la cámara si la jornada no está guardada o está en edición
        if not self.jornada_view.esta_lista_y_guardada():
            QMessageBox.warning(
                self,
                "Jornada Incompleta",
                "Debe guardar la configuración de la jornada antes de abrir la cámara.",
            )
            return
        # Cargar los embeddings de los alumnos registrados desde la base de datos
        alumnos_db = obtener_alumnos_con_fotos()
        self.facial_service.cargar_referencias_desde_db(alumnos_db)

        self.camera_open = True
        self.btn_abrir.setEnabled(False)
        self.btn_cerrar.setEnabled(True)
    
        # Iniciar el hilo de la cámara pasando el servicio de reconocimiento
        self.camera_worker = CameraWorker(facial_service=self.facial_service)
        self.camera_worker.frame_received.connect(self._actualizar_frame_panel)
        self.camera_worker.status_changed.connect(
            self._actualizar_texto_estado
        )
        self.camera_worker.alumno_reconocido.connect(
            self._procesar_registro_asistencia
        )

        self.camera_worker.start()
        self._mostrar_overlay("Escaneando...")

    def _cerrar_camara(self):
        self.camera_open = False
        self.overlay_timer.stop()
        self.lbl_overlay.hide()

        # Detener la cámara y liberar el recurso
        if self.camera_worker and self.camera_worker.isRunning():
            self.camera_worker.stop()
            self.camera_worker = None

        # Limpiar el panel y restaurar el texto inicial
        self.video_panel.clear()
        self.video_panel.setText("Apagado y Próximo")
        self._estado_fijo_hasta = 0.0
        self.lbl_estado.setText("Cámara cerrada.")

        self.evaluar_estado_botones()

    def _mostrar_overlay(self, texto, temporal=False):
        if not self.camera_open:
            return
        self.lbl_overlay.setText(texto)
        self.lbl_overlay.adjustSize()
        self._ubicar_overlay()
        self.lbl_overlay.show()
        self.lbl_overlay.raise_()
        if temporal:
            self.overlay_timer.start()
        else:
            self.overlay_timer.stop()

    def _ubicar_overlay(self):
        # Esquina inferior izquierda de la imagen de la cámara (centrada en el panel)
        margen = 10
        area = self.video_panel.contentsRect()
        pixmap = self.video_panel.pixmap()
        ancho, alto = area.width(), area.height()
        if pixmap is not None and not pixmap.isNull():
            ancho = min(ancho, pixmap.width())
            alto = min(alto, pixmap.height())
        x = area.x() + (area.width() - ancho) // 2 + margen
        y = (
            area.y()
            + (area.height() + alto) // 2
            - self.lbl_overlay.height()
            - margen
        )
        self.lbl_overlay.move(x, y)

    def eventFilter(self, obj, event):
        if obj is self.video_panel and event.type() == QEvent.Type.Resize:
            self._ubicar_overlay()
        return super().eventFilter(obj, event)

    def _actualizar_texto_estado(self, mensaje):
        # Mensajes del hilo de la cámara: no pisan el resultado de un registro reciente
        if not self.camera_open or time.monotonic() < self._estado_fijo_hasta:
            return
        self.lbl_estado.setText(mensaje)

    def _mostrar_resultado(self, mensaje):
        self.lbl_estado.setText(mensaje)
        self._estado_fijo_hasta = time.monotonic() + 3.0

    def _procesar_registro_asistencia(self, match_data, distancia):
        """Procesa las reglas de entrada, salida y tolerancia para un alumno reconocido."""
        jornada_id = self.jornada_view.jornada_id
        alumno_id = match_data["alumno_id"]
        nombre_alumno = match_data["nombre"]

        # 1. Consultar registro previo de asistencia
        asistencia = obtener_asistencia_alumno(jornada_id, alumno_id)

        if asistencia is None:
            # PRIMER RECONOCIMIENTO -> Registrar Entrada
            registrar_entrada_asistencia(jornada_id, alumno_id)
            self._mostrar_resultado(
                f"✅ Entrada registrada: {nombre_alumno}"
            )
            self._mostrar_overlay("Asistencia marcada", temporal=True)

        else:
            asistencia_id, hora_entrada, hora_salida = asistencia

            if hora_salida is not None:
                # Ya completó entrada y salida
                self._mostrar_resultado(
                    f"ℹ️ {nombre_alumno} ya completó su asistencia en esta jornada."
                )
            else:
                # SEGUNDO RECONOCIMIENTO -> Evaluar tolerancia de Salida (5 min antes)
                hora_salida_config = (
                    self.jornada_view.time_salida.time().toPython()
                )
                ahora = datetime.now().time()

                # Convertir a datetime para calcular los 5 minutos previos
                hoy = datetime.now().date()
                dt_salida_config = datetime.combine(hoy, hora_salida_config)
                dt_permitido = dt_salida_config - timedelta(minutes=5)
                dt_ahora = datetime.combine(hoy, ahora)

                if dt_ahora >= dt_permitido:
                    # Alcanzó el tiempo permitido -> Registrar Salida
                    registrar_salida_asistencia(asistencia_id)
                    self._mostrar_resultado(
                        f"✅ Salida registrada: {nombre_alumno}"
                    )
                    self._mostrar_overlay("Salida marcada", temporal=True)
                else:
                    minutos_restantes = int(
                        (dt_permitido - dt_ahora).total_seconds() / 60
                    )
                    self._mostrar_resultado(
                        f"⏳ Entrada ya registrada para {nombre_alumno}. Salida habilitada en {minutos_restantes} min."
                    )

    def _actualizar_frame_panel(self, q_image, raw_frame=None):
        if self.camera_open:
            pixmap = QPixmap.fromImage(q_image)
            # Escalar al área interna del panel (sin borde ni margen): si la imagen
            # fuera más grande que esa área, el panel crecería con cada fotograma
            scaled_pixmap = pixmap.scaled(
                self.video_panel.contentsRect().size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.video_panel.setPixmap(scaled_pixmap)
            self._ubicar_overlay()