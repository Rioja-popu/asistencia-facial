import os
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from repositories.student_repository import StudentRepository
from PySide6.QtCore import QDate
from PySide6.QtGui import QImage, QPixmap
from ui.camera_dialog import CameraCaptureDialog
from PySide6.QtWidgets import QDialog

class PhotoSectionWidget(QWidget):
    """Componente para gestionar la carga, previsualización y borrado de cada ángulo facial."""

    def __init__(self, titulo, angulo_key):
        super().__init__()
        self.angulo_key = angulo_key
        self.image_bytes = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 15)

        # Título de la sección
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #2c3e50;"
        )
        layout.addWidget(lbl_titulo)

        # Botones de acción
        btn_layout = QHBoxLayout()
        self.btn_cargar = QPushButton("Cargar Foto")
        self.btn_tomar = QPushButton("Tomar Foto")
        # En el __init__ de PhotoSectionWidget, después de crear self.btn_tomar:
        self.btn_tomar.clicked.connect(self._tomar_foto)

        for btn in (self.btn_cargar, self.btn_tomar):
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #219150; }
            """
            )
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        # Panel de visualización + Botón de Papelera
        preview_layout = QHBoxLayout()

        self.lbl_preview = QLabel("Sin imagen todavía")
        self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 6px;
                background-color: #f8f9fa;
                color: #7f8c8d;
            }
        """
        )
        preview_layout.addWidget(self.lbl_preview)

        # Botón Papelera (inicialmente oculto)
        self.btn_borrar = QPushButton("🗑️")
        self.btn_borrar.setFixedSize(35, 35)
        self.btn_borrar.setToolTip("Eliminar foto")
        self.btn_borrar.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """
        )
        self.btn_borrar.hide()
        preview_layout.addWidget(self.btn_borrar)
        preview_layout.addStretch()

        layout.addLayout(preview_layout)

        # Eventos
        self.btn_cargar.clicked.connect(self._cargar_foto)
        self.btn_borrar.clicked.connect(self.limpiar)

    def _tomar_foto(self):
        dialog = CameraCaptureDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            image_bytes = dialog.captured_frame_bytes
            if image_bytes:
                self.image_bytes = (
                    image_bytes  # o la variable donde guardes la foto
                )

                q_img = QImage.fromData(image_bytes)
                pixmap = QPixmap.fromImage(q_img)

                # Asegúrate de usar el nombre real de tu QLabel de vista previa
                self.lbl_preview.setPixmap(
                    pixmap.scaled(
                        self.lbl_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                # MOSTRAR EL BOTÓN DE BORRAR
                self.btn_borrar.show()

    def _cargar_foto(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen",
            "",
            "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp)",
        )
        if file_path:
            with open(file_path, "rb") as f:
                self.image_bytes = f.read()

            pixmap = QPixmap(file_path)
            self.lbl_preview.setPixmap(
                pixmap.scaled(
                    self.lbl_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.btn_borrar.show()

    def limpiar(self):
        self.image_bytes = None
        self.lbl_preview.clear()
        self.lbl_preview.setText("Sin imagen todavía")
        self.btn_borrar.hide()


class StudentRegisterView(QWidget):

    def __init__(self):
        super().__init__()
        self.repo = StudentRepository()

        # Layout principal con ScrollArea por si la pantalla es pequeña
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(30, 20, 30, 20)

        # Título
        title_label = QLabel("👤 Registrar Alumno")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;"
        )
        container_layout.addWidget(title_label)

        # -------------------------------------------------------------
        # FORMULARIO DE DATOS PERSONALES
        # -------------------------------------------------------------
        form_frame = QFrame()
        form_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel { font-weight: bold; color: #34495e; font-size: 13px; }
            QLineEdit, QDateEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                color: #2c3e50;
                background-color: #ffffff;
            }
        """
        )
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(10)

        self.input_nombre = QLineEdit()
        self.input_apellido = QLineEdit()
        self.input_dni = QLineEdit()
        self.input_carrera = QLineEdit()
        self.input_celular = QLineEdit()
        self.input_correo = QLineEdit()

        self.input_fecha_nac = QDateEdit()
        self.input_fecha_nac.setDisplayFormat("dd/MM/yyyy")
        self.input_fecha_nac.setCalendarPopup(True)
        self.input_fecha_nac.setDate(QDate.currentDate().addYears(-18))

        anio_actual = QDate.currentDate().year()
        self.input_anio_ingreso = QSpinBox()
        self.input_anio_ingreso.setRange(2000, anio_actual)  # Límite superior: año actual
        self.input_anio_ingreso.setValue(anio_actual)

        self.input_domicilio = QLineEdit()
        self.input_libreta = QLineEdit()

        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Apellido:", self.input_apellido)
        form_layout.addRow("DNI:", self.input_dni)
        form_layout.addRow("Carrera:", self.input_carrera)
        form_layout.addRow("Celular:", self.input_celular)
        form_layout.addRow("Correo Electrónico:", self.input_correo)
        form_layout.addRow("Fecha de Nacimiento:", self.input_fecha_nac)
        form_layout.addRow("Año de Ingreso:", self.input_anio_ingreso)
        form_layout.addRow("Domicilio:", self.input_domicilio)
        form_layout.addRow("Número de Libreta:", self.input_libreta)

        container_layout.addWidget(form_frame)

        # -------------------------------------------------------------
        # SECCIONES DE FOTOS
        # -------------------------------------------------------------
        photos_frame = QFrame()
        photos_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }
        """
        )
        photos_layout = QVBoxLayout(photos_frame)

        self.sec_frontal = PhotoSectionWidget(
            "Ángulo Frontal", "frontal"
        )
        self.sec_izquierdo = PhotoSectionWidget(
            "Ángulo Izquierdo", "lateral_izquierdo"
        )
        self.sec_derecho = PhotoSectionWidget(
            "Ángulo Derecho", "lateral_derecho"
        )

        photos_layout.addWidget(self.sec_frontal)
        photos_layout.addWidget(self.sec_izquierdo)
        photos_layout.addWidget(self.sec_derecho)

        container_layout.addWidget(photos_frame)

        # -------------------------------------------------------------
        # BOTÓN REGISTRAR
        # -------------------------------------------------------------
        self.btn_registrar = QPushButton("Registrar Alumno")
        self.btn_registrar.setStyleSheet(
            """
            QPushButton {
                background-color: #2980b9;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                margin-top: 15px;
            }
            QPushButton:hover { background-color: #3498db; }
        """
        )
        self.btn_registrar.clicked.connect(self._registrar_alumno)
        container_layout.addWidget(self.btn_registrar)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _registrar_alumno(self):
        # 1. Recopilar campos de texto
        nombre = self.input_nombre.text().strip()
        apellido = self.input_apellido.text().strip()
        dni = self.input_dni.text().strip()
        carrera = self.input_carrera.text().strip()
        celular = self.input_celular.text().strip()
        correo = self.input_correo.text().strip()
        fecha_nac = self.input_fecha_nac.date().toString("yyyy-MM-dd")
        anio_ingreso = self.input_anio_ingreso.value()
        domicilio = self.input_domicilio.text().strip()
        libreta = self.input_libreta.text().strip()

        # 2. Validar que no haya campos vacíos
        campos_textos = [
            nombre,
            apellido,
            dni,
            carrera,
            celular,
            correo,
            domicilio,
            libreta,
        ]
        if any(c == "" for c in campos_textos):
            QMessageBox.warning(
                self,
                "Campos Incompletos",
                "Existen campos obligatorios sin completar en el formulario.",
            )
            return

        # 3. Validar las 3 imágenes
        photos = {
            self.sec_frontal.angulo_key: self.sec_frontal.image_bytes,
            self.sec_izquierdo.angulo_key: self.sec_izquierdo.image_bytes,
            self.sec_derecho.angulo_key: self.sec_derecho.image_bytes,
        }

        if any(img is None for img in photos.values()):
            QMessageBox.warning(
                self,
                "Fotos Faltantes",
                "Debe cargar las tres imágenes (Frontal, Izquierda y Derecha).",
            )
            return

        # 4. Guardar en PostgreSQL
        try:
            student_data = (
                nombre,
                apellido,
                dni,
                carrera,
                celular,
                correo,
                fecha_nac,
                anio_ingreso,
                domicilio,
                libreta,
            )
            self.repo.save_student_with_photos(student_data, photos)

            QMessageBox.information(
                self,
                "Éxito",
                "El alumno fue registrado exitosamente.",
            )
            self._limpiar_formulario()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error en Base de Datos",
                f"Ocurrió un error al guardar el registro:\n{e}",
            )

    def _limpiar_formulario(self):
        """Reinicia el formulario a su estado inicial."""
        self.input_nombre.clear()
        self.input_apellido.clear()
        self.input_dni.clear()
        self.input_carrera.clear()
        self.input_celular.clear()
        self.input_correo.clear()
        self.input_domicilio.clear()
        self.input_libreta.clear()
        self.input_fecha_nac.setDate(QDate.currentDate().addYears(-18))
        self.input_anio_ingreso.setValue(QDate.currentDate().year())

        self.sec_frontal.limpiar()
        self.sec_izquierdo.limpiar()
        self.sec_derecho.limpiar()