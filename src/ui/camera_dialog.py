import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from services.camera_service import CameraWorker


ANCHO_VIDEO = 640


class CameraCaptureDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tomar foto del docente")

        self.captured_frame_bytes = None  # Almacenará la foto tomada en bytes

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

        # Panel del video: tiene exactamente el tamaño de la imagen, sin bordes
        self.video_label = QLabel("Iniciando cámara...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(ANCHO_VIDEO, ANCHO_VIDEO * 3 // 4)
        layout.addWidget(self.video_label)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(10, 10, 10, 10)
        self.btn_capturar = QPushButton("📸 Capturar Fotografía")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setProperty("rol", "neutro")

        btn_layout.addWidget(self.btn_capturar)
        btn_layout.addWidget(self.btn_cancelar)
        layout.addLayout(btn_layout)

        # Hilo de la cámara
        self.worker = CameraWorker()
        self.worker.frame_received.connect(self._update_frame)

        # Conexiones
        self.btn_capturar.clicked.connect(self._capturar)
        self.btn_cancelar.clicked.connect(self.reject)

        self.last_raw_frame = None
        self.worker.start()

    def _update_frame(self, image: QImage, raw_frame):
        self.last_raw_frame = raw_frame
        pixmap = QPixmap.fromImage(image).scaledToWidth(
            ANCHO_VIDEO, Qt.TransformationMode.SmoothTransformation
        )
        # El panel toma la proporción real de la cámara, así no sobran bordes
        if self.video_label.size() != pixmap.size():
            self.video_label.setFixedSize(pixmap.size())
        self.video_label.setPixmap(pixmap)

    def _capturar(self):
        if self.last_raw_frame is not None:
            # Codificar la imagen capturada a JPEG
            _, buffer = cv2.imencode(".jpg", self.last_raw_frame)
            self.captured_frame_bytes = buffer.tobytes()
            self._stop_camera()
            self.accept()

    def _stop_camera(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()

    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)

    def reject(self):
        self._stop_camera()
        super().reject()