from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from ui.jornada_view import JornadaView
from ui.student_register_view import StudentRegisterView
from ui.attendance_view import AttendanceView

class WelcomeWindow(QWidget):
    def __init__(self, nombre_usuario):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.setWindowTitle("Sistema de Asistencia Facial")
        self.resize(800, 500)

        # Layout Principal (Dividido horizontalmente: Menú a la izquierda, Área de contenido a la derecha)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -----------------------------------------------------------------
        # ZONA AMARILLA: Menú Lateral
        # -----------------------------------------------------------------
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(220)
        sidebar_widget.setStyleSheet(
            """
            QWidget {
                background-color: #2c3e50;
            }
            QPushButton {
                background-color: transparent;
                color: #ecf0f1;
                text-align: left;
                padding: 12px 15px;
                font-size: 13px;
                border: none;
                border-radius: 5px;
                margin: 2px 8px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #2980b9;
                font-weight: bold;
            }
        """
        )

        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(5, 20, 5, 20)
        sidebar_layout.setSpacing(10)

        # Saludo en la barra lateral
        user_label = QLabel(f"Usuario: {self.nombre_usuario}")
        user_label.setStyleSheet(
            "color: #bdc3c7; font-size: 12px; margin-bottom: 15px; padding-left: 10px;"
        )
        sidebar_layout.addWidget(user_label)

        # Botones del menú lateral
        self.btn_asistencia = QPushButton("📷  Asistencia por Captura")
        self.btn_jornada = QPushButton("⚙️  Configuración de Jornada")
        self.btn_registrar = QPushButton("👤  Registrar Alumno")

        for btn in (self.btn_asistencia, self.btn_jornada, self.btn_registrar):
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()  # Empuja los botones hacia arriba

        # -----------------------------------------------------------------
        # ZONA VERDE: Área de Contenido Dinámica (QStackedWidget)
        # -----------------------------------------------------------------
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #f8f9fa;")

        # Crear vistas placeholder para cada pantalla
        self.view_asistencia = self._crear_vista_placeholder(
            "📷 Asistencia por Captura Facial",
            f"Bienvenido {self.nombre_usuario}.\nMódulo de captura facial listo.",
        )
        self.view_jornada = JornadaView()

        self.view_asistencia = AttendanceView(jornada_view=self.view_jornada)
        
        self.view_registrar = StudentRegisterView()
        

        # Agregar las vistas al contenedor apilado
        self.content_area.addWidget(self.view_asistencia)  # Índice 0
        self.content_area.addWidget(self.view_jornada)  # Índice 1
        self.content_area.addWidget(self.view_registrar)  # Índice 2

        # -----------------------------------------------------------------
        # Conexiones de Eventos
        # -----------------------------------------------------------------
        self.btn_asistencia.clicked.connect(lambda: self._cambiar_vista(0))
        self.btn_jornada.clicked.connect(lambda: self._cambiar_vista(1))
        self.btn_registrar.clicked.connect(lambda: self._cambiar_vista(2))

        # Ensamblar estructura final
        main_layout.addWidget(sidebar_widget)
        main_layout.addWidget(self.content_area)

        # Cargar vista por defecto
        self._cambiar_vista(0)

    def _cambiar_vista(self, index):
        """Cambia el widget visible del panel central y actualiza los botones."""
        if index != 0 and hasattr(self, "view_asistencia"):
            if self.view_asistencia.camera_open:
                self.view_asistencia._cerrar_camara()
        self.content_area.setCurrentIndex(index)

        # Marcar visualmente solo el botón activo
        self.btn_asistencia.setChecked(index == 0)
        self.btn_jornada.setChecked(index == 1)
        self.btn_registrar.setChecked(index == 2)

    def _crear_vista_placeholder(self, titulo, descripcion):
        """Crea una vista base provisional para el contenido central."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(titulo)
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;"
        )

        desc_label = QLabel(descripcion)
        desc_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        return widget