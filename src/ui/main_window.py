from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from repositories import user_repository
from services import usuario_service
from ui import iconos, theme
from ui.actividades_view import ActividadesView
from ui.ausencias_view import AusenciasView
from ui.contrasenia_dialog import ContraseniaDialog
from ui.catedras_view import CatedrasView
from ui.docentes_view import DocentesView
from ui.horarios_view import HorariosView
from ui.informes_view import InformesView
from ui.inicio_view import InicioView
from ui.marcacion_view import MarcacionView
from ui.no_laborables_view import NoLaborablesView
from ui.usuarios_view import UsuariosView


class MainWindow(QWidget):
    """Ventana principal: menú lateral con el escudo y las secciones del sistema."""

    def __init__(self, usuario, al_cerrar_sesion=None):
        super().__init__()
        self.usuario_id = usuario["id"]
        self.nombre_usuario = usuario["nombre_usuario"]
        self.al_cerrar_sesion = al_cerrar_sesion
        self.cerrando_sesion = False
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
                padding: 11px 12px; font-size: 13px; font-weight: normal;
                border: none; border-left: 4px solid transparent; border-radius: 0px;
            }}
            QPushButton:hover {{ background-color: {theme.AZUL_CLARO}; }}
            QPushButton[rol="cuenta"] {{ padding: 8px 12px; font-size: 12px; color: #c9d6e8; }}
            QPushButton[rol="cuenta"]:hover {{ color: #ffffff; }}
            QPushButton:checked {{
                background-color: #1d4a80; color: {theme.DORADO}; font-weight: bold;
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
            ("Inicio", "inicio", InicioView()),
            ("Marcación", "marcacion", self.view_marcacion),
            ("Docentes", "docentes", DocentesView()),
            ("Carreras y cátedras", "catedras", CatedrasView()),
            ("Horarios", "horarios", HorariosView()),
            ("Actividades especiales", "actividades", ActividadesView(self.nombre_usuario)),
            ("Ausencias", "ausencias", AusenciasView(self.usuario_id)),
            ("Feriados y recesos", "feriados", NoLaborablesView(self.usuario_id)),
            ("Informes", "informes", InformesView(self.usuario_id, self.nombre_usuario)),
        ]
        if usuario["rol"] == usuario_service.ADMINISTRADOR:
            secciones.append(("Usuarios", "usuarios", UsuariosView(self.usuario_id)))

        self.content_area = QStackedWidget()
        self.content_area.setObjectName("contenido")
        self.content_area.setStyleSheet(
            f"QStackedWidget#contenido {{ background-color: {theme.FONDO}; }}"
        )
        self.botones = []
        for indice, (texto, icono, vista) in enumerate(secciones):
            btn = QPushButton("  " + texto)
            btn.setIcon(iconos.icono(icono))
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.clicked.connect(lambda _=False, i=indice: self._cambiar_vista(i))
            sidebar_layout.addWidget(btn)
            self.botones.append(btn)
            self.content_area.addWidget(vista)

        sidebar_layout.addStretch()
        lbl_usuario = QLabel(
            f"{self.nombre_usuario}\n{usuario_service.ROLES[usuario['rol']]}"
        )
        lbl_usuario.setObjectName("usuario")
        lbl_usuario.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(lbl_usuario)
        sidebar_layout.addSpacing(6)
        for texto, icono, accion in (
            ("Cambiar contraseña", "llave", self._cambiar_contrasenia),
            ("Cerrar sesión", "salir", self._cerrar_sesion),
        ):
            btn = QPushButton("  " + texto)
            btn.setProperty("rol", "cuenta")
            btn.setIcon(iconos.icono(icono, "#c9d6e8"))
            btn.setIconSize(QSize(16, 16))
            btn.clicked.connect(accion)
            sidebar_layout.addWidget(btn)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.content_area)
        self._cambiar_vista(0)

    def _cambiar_vista(self, index):
        # La cámara sólo queda abierta mientras se está en la pantalla de marcación
        vista = self.content_area.widget(index)
        if vista is not self.view_marcacion and self.view_marcacion.camera_open:
            self.view_marcacion._cerrar_camara()
        if hasattr(vista, "refrescar"):
            vista.refrescar()
        self.content_area.setCurrentIndex(index)
        for i, btn in enumerate(self.botones):
            btn.setChecked(i == index)

    def _cambiar_contrasenia(self):
        try:
            guardada = user_repository.obtener(self.usuario_id)["contrasenia"]
        except Exception as e:
            theme.error_bd(self, e)
            return
        dialogo = ContraseniaDialog(
            "Cambiar contraseña",
            f"Contraseña del usuario \"{self.nombre_usuario}\".",
            guardada, self,
        )
        if not dialogo.exec():
            return
        try:
            user_repository.guardar_contrasenia(self.usuario_id, dialogo.nueva)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.informar(self, "Contraseña cambiada", "Usá la contraseña nueva la próxima vez.")

    def _cerrar_sesion(self):
        if not theme.confirmar(self, "Cerrar sesión", "¿Cerrar la sesión y volver al inicio?"):
            return
        self.cerrando_sesion = True
        self.close()

    def closeEvent(self, event):
        if self.view_marcacion.camera_open:
            self.view_marcacion._cerrar_camara()
        self.view_marcacion.esperar_cierre()
        super().closeEvent(event)
        if self.al_cerrar_sesion:
            if self.cerrando_sesion:
                self.al_cerrar_sesion()
            else:
                # Se cerró la ventana: termina la aplicación, no queda el login oculto
                QApplication.quit()
