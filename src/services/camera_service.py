import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


class CameraWorker(QThread):
    # Señal para emitir cada fotograma procesado a la interfaz
    frame_received = Signal(QImage, object)  # (QImage para UI, ndarray de cv2)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._is_running = False

    def run(self):
        self._is_running = True
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            self._is_running = False
            return

        while self._is_running:
            ret, frame = cap.read()
            if ret:
                # Convertir de BGR (OpenCV) a RGB (Qt)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w

                q_image = QImage(
                    frame_rgb.data,
                    w,
                    h,
                    bytes_per_line,
                    QImage.Format.Format_RGB888,
                )
                self.frame_received.emit(q_image, frame)

            self.msleep(30)  # ~30 FPS

        cap.release()

    def stop(self):
        self._is_running = False
        self.wait()