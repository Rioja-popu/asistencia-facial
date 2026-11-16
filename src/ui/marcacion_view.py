import time
from datetime import datetime

from PySide6.QtCore import QEvent, QRect, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from repositories import asistencia_repository, ausencia_repository, docente_repository
from services import marcacion_service
from services.camera_service import CameraWorker
from services.facial_service import FacialRecognitionService
from ui import theme
from ui.confirmar_marcacion_dialog import ConfirmarMarcacionDialog


class ContenedorVideo(QWidget):
    """Mantiene el panel de video centrado y con la proporción de la cámara,
    para que la imagen lo ocupe entero y no sobren bordes a los costados."""

    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.proporcion = 4 / 3
        panel.setParent(self)
        self.setMinimumHeight(300)

    def fijar_proporcion(self, ancho, alto):
        proporcion = ancho / alto
        if abs(proporcion - self.proporcion) > 0.01:
            self.proporcion = proporcion
            self._acomodar()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._acomodar()

    def _acomodar(self):
        alto = self.height()
        ancho = round(alto * self.proporcion)
        if ancho > self.width():
            ancho = self.width()
            alto = round(ancho / self.proporcion)
        self.panel.setGeometry(
            QRect((self.width() - ancho) // 2, (self.height() - alto) // 2, ancho, alto)
        )


class MarcacionView(QWidget):
    """Marcación de entrada y salida de docentes por reconocimiento facial."""

    def __init__(self):
        super().__init__()
        self.camera_open = False
        self.camera_worker = None
        self._worker_cerrando = None
        self.facial_service = FacialRecognitionService()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.addWidget(theme.etiqueta("Marcación de asistencia docente"))
        main_layout.addWidget(
            theme.etiqueta(
                "El docente se ubica frente a la cámara, el sistema lo identifica y "
                "le pide confirmar la entrada o la salida.",
                "subtitulo",
            )
        )

        btn_layout = QHBoxLayout()
        self.btn_abrir = theme.boton("Abrir cámara", "confirmar", self._abrir_camara)
        self.btn_cerrar = theme.boton("Cerrar cámara", "secundario", self._cerrar_camara)
        self.btn_cerrar.setEnabled(False)
        btn_layout.addWidget(self.btn_abrir)
        btn_layout.addWidget(self.btn_cerrar)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.video_panel = QLabel("Cámara apagada")
        self.video_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_panel.setStyleSheet(
            f"""
            QLabel {{
                border: 1px solid #c5ced9;
                background-color: #ffffff;
                color: {theme.GRIS};
                font-size: 16px;
                font-weight: bold;
            }}
        """
        )
        self.contenedor_video = ContenedorVideo(self.video_panel)

        # Cartel superpuesto en la esquina inferior izquierda de la imagen
        self.lbl_overlay = QLabel(self.video_panel)
        self.lbl_overlay.setStyleSheet(
            """
            QLabel {
                border: none;
                border-radius: 4px;
                background-color: rgba(20, 53, 96, 200);
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

        self.overlay_timer = QTimer(self)
        self.overlay_timer.setSingleShot(True)
        self.overlay_timer.setInterval(3000)
        self.overlay_timer.timeout.connect(lambda: self._mostrar_overlay("Escaneando..."))

        self.lbl_estado = QLabel("Cámara cerrada.")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {theme.AZUL}; margin-top: 10px;"
        )

        main_layout.addSpacing(10)
        main_layout.addWidget(self.contenedor_video, 1)
        main_layout.addWidget(self.lbl_estado)

        # Mientras no pase este instante, el resultado de una marcación queda en pantalla
        self._estado_fijo_hasta = 0.0

    # ------------------------------------------------------------------ cámara
    def _abrir_camara(self):
        try:
            docentes = docente_repository.obtener_docentes_con_fotos()
        except Exception as e:
            theme.error_bd(self, e)
            return
        if not docentes:
            theme.avisar(
                self, "Sin docentes",
                "No hay docentes activos registrados. Cargalos en la sección Docentes.",
            )
            return
        self.camera_open = True
        self.btn_abrir.setEnabled(False)
        self.btn_cerrar.setEnabled(True)

        self.camera_worker = CameraWorker(
            facial_service=self.facial_service, docentes=docentes
        )
        self.camera_worker.frame_received.connect(self._actualizar_frame_panel)
        self.camera_worker.status_changed.connect(self._actualizar_texto_estado)
        self.camera_worker.docente_reconocido.connect(self._procesar_reconocimiento)
        self.camera_worker.start()
        self.video_panel.setText("Preparando la cámara...")

    def _cerrar_camara(self):
        self.camera_open = False
        self.overlay_timer.stop()
        self.lbl_overlay.hide()
        worker, self.camera_worker = self.camera_worker, None
        if worker and worker.isRunning():
            # No se espera al hilo: si todavía está cargando el modelo o encendiendo
            # la cámara, la ventana se congelaría. Se vuelve a habilitar "Abrir
            # cámara" recién cuando el hilo terminó.
            self._worker_cerrando = worker
            worker.finished.connect(self._camara_liberada)
            worker.pedir_detencion()
        self.video_panel.clear()
        self.video_panel.setText("Cámara apagada")
        self._estado_fijo_hasta = 0.0
        self.lbl_estado.setText("Cámara cerrada.")
        self.btn_abrir.setEnabled(self._worker_cerrando is None)
        self.btn_cerrar.setEnabled(False)

    def esperar_cierre(self):
        """Al cerrar la aplicación sí hay que esperar a que termine el hilo."""
        if self._worker_cerrando is not None:
            self._worker_cerrando.wait()

    def _camara_liberada(self):
        self._worker_cerrando = None
        if not self.camera_open:
            self.btn_abrir.setEnabled(True)

    # ------------------------------------------------------------- marcación
    def _procesar_reconocimiento(self, match_data, distancia):
        """Aplica las reglas al docente reconocido y, si corresponde, pide confirmación.

        El hilo de la cámara ya pausó el reconocimiento antes de emitir la señal;
        acá se reanuda siempre al terminar, se haya confirmado o no.
        """
        try:
            self._proponer_y_confirmar(match_data["docente_id"], match_data["nombre"])
        except Exception as e:
            theme.error_bd(self, e)
        finally:
            if self.camera_worker:
                self.camera_worker.reanudar_reconocimiento()

    def _proponer_y_confirmar(self, docente_id, nombre):
        if not docente_repository.docente_esta_activo(docente_id):
            self._mostrar_resultado(f"{nombre}: el docente está dado de baja.")
            return

        ahora = datetime.now()
        hoy = ahora.date()
        obligaciones = asistencia_repository.obtener_obligaciones(docente_id, hoy)
        propuesta = marcacion_service.proponer_marcacion(obligaciones, ahora)

        if propuesta["operacion"] is None:
            # Nada para registrar: se explica el motivo y no se toca la base
            self._mostrar_resultado(f"{nombre}: {propuesta['motivo']}")
            self._mostrar_overlay("Sin marcación", temporal=True)
            return

        tiene_ausencia = hoy in ausencia_repository.obtener_ausencias(docente_id, hoy, hoy)
        self._mostrar_overlay("Esperando confirmación...")
        foto = docente_repository.obtener_fotos(docente_id).get("frontal")
        confirmado = self._pedir_confirmacion(nombre, foto, propuesta, ahora, tiene_ausencia)
        if not confirmado:
            self._mostrar_resultado(f"Marcación cancelada por {nombre}. No se registró nada.")
            self._mostrar_overlay("Marcación cancelada", temporal=True)
            return

        if propuesta["operacion"] == marcacion_service.ENTRADA:
            asistencia_repository.registrar_entradas(
                docente_id, hoy, propuesta["items"], ahora
            )
            tarde = any(item["tardanza"] for item in propuesta["items"])
            self._mostrar_resultado(
                f"Entrada registrada: {nombre}" + (" (tardanza)" if tarde else " (en horario)")
            )
            self._mostrar_overlay("Entrada marcada", temporal=True)
        else:
            asistencia_repository.registrar_salidas(propuesta["items"], ahora)
            antes = any(item["salida_anticipada"] for item in propuesta["items"])
            self._mostrar_resultado(
                f"Salida registrada: {nombre}" + (" (salida anticipada)" if antes else "")
            )
            self._mostrar_overlay("Salida marcada", temporal=True)

    def _pedir_confirmacion(self, nombre, foto, propuesta, ahora, tiene_ausencia):
        """Modal con OK y Cancelar. Devuelve True sólo si se eligió OK."""
        modal = ConfirmarMarcacionDialog(nombre, foto, propuesta, ahora, tiene_ausencia, self)
        return modal.exec() == QDialog.DialogCode.Accepted

    # ---------------------------------------------------------------- mensajes
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
        margen = 10
        area = self.video_panel.contentsRect()
        pixmap = self.video_panel.pixmap()
        ancho, alto = area.width(), area.height()
        if pixmap is not None and not pixmap.isNull():
            ancho = min(ancho, pixmap.width())
            alto = min(alto, pixmap.height())
        x = area.x() + (area.width() - ancho) // 2 + margen
        y = area.y() + (area.height() + alto) // 2 - self.lbl_overlay.height() - margen
        self.lbl_overlay.move(x, y)

    def eventFilter(self, obj, event):
        if obj is self.video_panel and event.type() == QEvent.Type.Resize:
            self._ubicar_overlay()
        return super().eventFilter(obj, event)

    def _actualizar_texto_estado(self, mensaje):
        # Mensajes del hilo de la cámara: no pisan el resultado de una marcación reciente
        if not self.camera_open or time.monotonic() < self._estado_fijo_hasta:
            return
        self.lbl_estado.setText(mensaje)

    def _mostrar_resultado(self, mensaje):
        self.lbl_estado.setText(mensaje)
        self._estado_fijo_hasta = time.monotonic() + 4.0

    def _actualizar_frame_panel(self, q_image, raw_frame=None):
        if self.camera_open:
            pixmap = QPixmap.fromImage(q_image)
            self.contenedor_video.fijar_proporcion(pixmap.width(), pixmap.height())
            scaled_pixmap = pixmap.scaled(
                self.video_panel.contentsRect().size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.video_panel.setPixmap(scaled_pixmap)
            if self.lbl_overlay.isHidden():
                # Primera imagen: la cámara ya está lista
                self._mostrar_overlay("Escaneando...")
            self._ubicar_overlay()
