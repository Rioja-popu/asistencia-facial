import time
import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


class CameraWorker(QThread):
    # Señales para comunicar con la UI
    frame_received = Signal(QImage, object)  # (QImage para la UI, fotograma original de cv2)
    status_changed = Signal(str)  # Mensaje de estado ("Esperando rostro", etc.)
    alumno_reconocido = Signal(
        dict, float
    )  # Emitir datos del alumno y la distancia si pasa el umbral

    def __init__(self, facial_service=None, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.facial_service = facial_service
        self._is_running = False

        # Cargar clasificador de rostros Haar Cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Control de frecuencia de procesamiento (cada 2 segundos)
        self.last_recognition_time = 0
        self.recognition_interval = 2.0  # segundos
        self.is_processing = False

    def run(self):
        self._is_running = True
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            self.status_changed.emit("Error: No se pudo abrir la cámara")
            self._is_running = False
            return

        while self._is_running:
            ret, frame = cap.read()
            if not ret:
                continue

            # Fotograma original, sin espejo ni dibujos (se usa al tomar la foto de registro)
            raw_frame = frame

            # Volteo horizontal para efecto espejo
            frame = cv2.flip(frame, 1)

            # Detección de rostros: sólo en asistencia, no al tomar la foto de registro
            faces = []
            if self.facial_service:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
                )

            num_faces = len(faces)

            if num_faces == 0:
                self.status_changed.emit("Esperando rostro...")
            elif num_faces > 1:
                self.status_changed.emit("Más de un rostro detectado")
            elif num_faces == 1:
                x, y, w, h = faces[0]

                # Dibujar rectángulo alrededor del rostro
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                current_time = time.time()
                # Verificar intervalo de 2 segundos y que no haya un proceso en curso
                if (
                    self.facial_service
                    and not self.is_processing
                    and (
                        current_time - self.last_recognition_time
                        >= self.recognition_interval
                    )
                ):

                    self.is_processing = True
                    self.last_recognition_time = current_time
                    self.status_changed.emit(
                        "Procesando reconocimiento facial..."
                    )

                    # Recortar el rostro del fotograma original (sin espejo ni rectángulo),
                    # igual que las fotos de registro
                    x_raw = frame.shape[1] - x - w
                    face_crop = raw_frame[y : y + h, x_raw : x_raw + w]

                    # Procesar reconocimiento
                    match, distance = self.facial_service.reconocer_rostro(
                        face_crop, threshold=0.40
                    )

                    if match:
                        self.status_changed.emit(
                            f"Alumno reconocido: {match['nombre']} (Dist: {distance:.2f})"
                        )
                        self.alumno_reconocido.emit(match, distance)
                    else:
                        self.status_changed.emit(
                            f"Rostro no reconocido (Dist mínima: {distance:.2f})"
                        )

                    self.is_processing = False

            # Convertir fotograma a QImage para la interfaz
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h_img, w_img, ch = frame_rgb.shape
            bytes_per_line = ch * w_img

            q_image = QImage(
                frame_rgb.data,
                w_img,
                h_img,
                bytes_per_line,
                QImage.Format.Format_RGB888,
            )
            self.frame_received.emit(q_image, raw_frame)

            self.msleep(30)  # ~30 FPS

        cap.release()

    def stop(self):
        self._is_running = False
        self.wait()