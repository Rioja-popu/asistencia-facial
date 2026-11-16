from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from repositories.user_repository import UserRepository
from ui import theme


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.repo = UserRepository()
        self.main_window = None

        self.setWindowTitle(f"{theme.SISTEMA} - Inicio de sesión")
        self.setWindowIcon(QIcon(theme.RUTA_ESCUDO))
        self.resize(420, 480)
        self.setObjectName("login")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#login {{ background-color: {theme.FONDO}; }}")

        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText("Usuario / Email / DNI / CUIL")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.iniciar_sesion)

        self.login_button = theme.boton("Iniciar sesión", al_hacer_clic=self.iniciar_sesion)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(12)
        layout.addWidget(theme.escudo(150))
        for texto, nombre in ((theme.INSTITUCION, "titulo"), (theme.SISTEMA, "subtitulo")):
            lbl = QLabel(texto)
            lbl.setObjectName(nombre)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setWordWrap(True)
            layout.addWidget(lbl)
        layout.addSpacing(10)
        layout.addWidget(self.identifier_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addStretch()

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
