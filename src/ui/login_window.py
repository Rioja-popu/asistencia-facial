from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from repositories.user_repository import UserRepository
from ui import theme


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.repo = UserRepository()
        self.main_window = None

        self.setWindowTitle(f"{theme.SISTEMA} - Inicio de sesión")
        self.setWindowIcon(QIcon(theme.RUTA_ESCUDO))
        self.resize(780, 460)
        self.setObjectName("login")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            QWidget#login {{ background-color: #ffffff; }}
            QWidget#identidad {{ background-color: {theme.AZUL}; }}
            QWidget#identidad QLabel {{ background: transparent; color: #ffffff; }}
            QLabel#institucion {{ font-size: 19px; font-weight: bold; }}
            QLabel#sistema {{ font-size: 14px; color: {theme.DORADO}; }}
            QFrame#acento {{ background-color: {theme.DORADO}; border: none; }}
            QLabel#bienvenida {{ font-size: 22px; font-weight: bold; color: {theme.AZUL}; }}
            QLineEdit {{ padding: 9px 10px; }}
            QPushButton {{ padding: 10px 14px; font-size: 14px; }}
            """
        )

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Usuario / Email / DNI / CUIL")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.iniciar_sesion)

        self.login_button = theme.boton("Iniciar sesión", al_hacer_clic=self.iniciar_sesion)

        identidad = QWidget()
        identidad.setObjectName("identidad")
        identidad.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        izquierda = QVBoxLayout(identidad)
        izquierda.setContentsMargins(30, 30, 30, 30)
        izquierda.setSpacing(10)
        izquierda.addStretch()
        izquierda.addWidget(theme.escudo(170))
        izquierda.addSpacing(8)
        for texto, nombre in ((theme.INSTITUCION, "institucion"), (theme.SISTEMA, "sistema")):
            lbl = QLabel(texto)
            lbl.setObjectName(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            izquierda.addWidget(lbl)
            if nombre == "institucion":
                acento = QFrame()
                acento.setObjectName("acento")
                acento.setFixedSize(60, 3)
                izquierda.addWidget(acento, alignment=Qt.AlignmentFlag.AlignHCenter)
        izquierda.addStretch()

        formulario = QVBoxLayout()
        formulario.setContentsMargins(45, 30, 45, 30)
        formulario.setSpacing(12)
        formulario.addStretch()
        formulario.addWidget(theme.etiqueta("Iniciar sesión", "bienvenida"))
        formulario.addWidget(
            theme.etiqueta("Ingresá con tu usuario del personal administrativo.", "subtitulo")
        )
        formulario.addSpacing(10)
        formulario.addWidget(self.identifier_input)
        formulario.addWidget(self.password_input)
        formulario.addSpacing(4)
        formulario.addWidget(self.login_button)
        formulario.addStretch()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(identidad, 1)
        layout.addLayout(formulario, 1)

    def iniciar_sesion(self):
        identificador = self.identifier_input.text().strip()
        contrasenia = self.password_input.text().strip()

        if identificador == "" or contrasenia == "":
            QMessageBox.warning(self, "Datos incompletos", "Ingrese usuario y contraseña.")
            return

        try:
            usuario = self.repo.find_by_credentials(identificador, contrasenia)
        except Exception as e:
            theme.error_bd(self, e)
            return

        if usuario is None:
            QMessageBox.critical(self, "Error", "Credenciales incorrectas.")
            return

        # Import diferido: la ventana principal carga el reconocimiento facial, que tarda
        from ui.main_window import MainWindow

        self.main_window = MainWindow(usuario[0], usuario[1])
        self.main_window.show()
        self.close()
