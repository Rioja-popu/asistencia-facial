import os
import sys

# Agregar el directorio 'src' al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from ui import theme
from ui.login_window import LoginWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.ESTILO_APP)

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
