import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from services.camera_service import CameraWorker


class CameraCaptureDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tomar Foto - Captura de Rostro")
        self.setFixedSize(640, 520)

        self.captured_frame_bytes = None  # Almacenará la foto tomada en bytes

        layout = QVBoxLayout(self)

        # Panel donde se muestra el video en vivo
        self.video_label = QLabel("Iniciando cámara...")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000; color: #fff;")
        layout.addWidget(self.video_label)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_capturar = QPushButton("📸 Capturar Fotografía")
        self.btn_capturar.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold; padding: 10px;"
        )
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet(
            "background-color: #e74c3c; color: white; padding: 10px;"
        )

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

    def _update_frame(self, q_image, raw_frame):
        self.last_raw_frame = raw_frame
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled_pixmap)

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