from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from ui.actividades_view import ActividadesView
from ui.ausencias_view import AusenciasView
from ui.catedras_view import CatedrasView
from ui.docentes_view import DocentesView
from ui.horarios_view import HorariosView
from ui.informes_view import InformesView
from ui.marcacion_view import MarcacionView


class MainWindow(QWidget):
    """Ventana principal: menú lateral con el escudo y las secciones del sistema."""

    def __init__(self, usuario_id, nombre_usuario):
        super().__init__()
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.setWindowTitle(f"{theme.SISTEMA} - {theme.INSTITUCION}")
        self.setWindowIcon(QIcon(theme.RUTA_ESCUDO))
        self.resize(1180, 760)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("menu")
        sidebar.setFixedWidth(240)
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setStyleSheet(
            f"""
            QWidget#menu {{ background-color: {theme.AZUL}; }}
            QLabel {{ background: transparent; color: #ffffff; }}
            QLabel#institucion {{ font-size: 13px; font-weight: bold; }}
            QLabel#sistema {{ font-size: 12px; color: {theme.DORADO}; }}
            QLabel#usuario {{ font-size: 12px; color: #c9d6e8; }}
            QPushButton {{
                background-color: transparent; color: #ffffff; text-align: left;
                padding: 11px 14px; font-size: 13px; font-weight: normal;
                border: none; border-left: 4px solid transparent; border-radius: 0px;
            }}
            QPushButton:hover {{ background-color: {theme.AZUL_CLARO}; }}
            QPushButton:checked {{
                background-color: {theme.AZUL_CLARO}; font-weight: bold;
                border-left: 4px solid {theme.DORADO};
            }}
        """
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 20, 0, 15)
        sidebar_layout.setSpacing(2)

        sidebar_layout.addWidget(theme.escudo(110))
        for texto, nombre in ((theme.INSTITUCION, "institucion"), (theme.SISTEMA, "sistema")):
            lbl = QLabel(texto)
            lbl.setObjectName(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            sidebar_layout.addWidget(lbl)
        sidebar_layout.addSpacing(18)

        self.view_marcacion = MarcacionView()
        secciones = [
            ("Marcación", self.view_marcacion),
            ("Docentes", DocentesView()),
            ("Carreras y cátedras", CatedrasView()),
            ("Horarios", HorariosView()),
            ("Actividades especiales", ActividadesView()),
            ("Ausencias", AusenciasView(self.usuario_id)),
            ("Informes", InformesView(self.nombre_usuario)),
        ]

        self.content_area = QStackedWidget()
        self.content_area.setObjectName("contenido")
        self.content_area.setStyleSheet(
            f"QStackedWidget#contenido {{ background-color: {theme.FONDO}; }}"
        )
        self.botones = []
        for indice, (texto, vista) in enumerate(secciones):
            btn = QPushButton(texto)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=indice: self._cambiar_vista(i))
            sidebar_layout.addWidget(btn)
            self.botones.append(btn)
            self.content_area.addWidget(vista)

        sidebar_layout.addStretch()
        lbl_usuario = QLabel(f"Usuario: {self.nombre_usuario}")
        lbl_usuario.setObjectName("usuario")
        lbl_usuario.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_usuario)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_area)
        self._cambiar_vista(0)

    def _cambiar_vista(self, index):
        # La cámara sólo queda abierta mientras se está en la pantalla de marcación
        if index != 0 and self.view_marcacion.camera_open:
            self.view_marcacion._cerrar_camara()
        vista = self.content_area.widget(index)
        if hasattr(vista, "refrescar"):
            vista.refrescar()
        self.content_area.setCurrentIndex(index)
        for i, btn in enumerate(self.botones):
            btn.setChecked(i == index)

    def closeEvent(self, event):
        if self.view_marcacion.camera_open:
            self.view_marcacion._cerrar_camara()
        super().closeEvent(event)
