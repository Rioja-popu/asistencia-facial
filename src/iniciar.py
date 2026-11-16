"""Lanzador del acceso directo: levanta la base de datos si hace falta y abre la aplicación.

Se ejecuta con pythonw (sin consola), por eso los mensajes van a ventanas y a iniciar.log.
"""

import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout is None or sys.stderr is None:
    # pythonw no tiene consola: sin esto, cualquier biblioteca que escriba en ella falla
    sys.stdout = sys.stderr = open(
        os.path.join(RAIZ, "iniciar.log"), "w", encoding="utf-8", buffering=1
    )

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QVBoxLayout, QWidget

from config.database import get_connection
from ui import theme

DOCKER_DESKTOP = os.path.join(
    os.environ.get("ProgramFiles", r"C:\Program Files"), "Docker", "Docker", "Docker Desktop.exe"
)
ESPERA_DOCKER = 180
ESPERA_BASE = 90
SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def base_disponible():
    try:
        get_connection().close()
        return True
    except Exception:
        return False


def _ejecutar(comando, pausa):
    """Corre un comando sin abrir consola. True si terminó bien."""
    try:
        proceso = subprocess.Popen(
            comando, cwd=RAIZ, creationflags=SIN_VENTANA,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return False
    while proceso.poll() is None:
        pausa(0.2)
    return proceso.returncode == 0


def _esperar(condicion, segundos, pausa):
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if condicion():
            return True
        pausa(1)
    return False


def preparar_base(avisar=lambda texto: None, pausa=time.sleep):
    """Deja la base lista para usar. Devuelve None, o el motivo por el que no se pudo."""
    if base_disponible():
        return None
    levantar = ["docker", "compose", "up", "-d"]
    avisar("Iniciando la base de datos...")
    if not _ejecutar(levantar, pausa):
        if not os.path.exists(DOCKER_DESKTOP):
            return "No se encontró Docker Desktop. Instalalo o abrilo y volvé a intentar."
        avisar("Abriendo Docker Desktop. Puede tardar uno o dos minutos...")
        subprocess.Popen([DOCKER_DESKTOP], creationflags=SIN_VENTANA)
        if not _esperar(lambda: _ejecutar(["docker", "info"], pausa), ESPERA_DOCKER, pausa):
            return "Docker Desktop no terminó de iniciar. Abrilo a mano y volvé a intentar."
        avisar("Iniciando la base de datos...")
        if not _ejecutar(levantar, pausa):
            return "No se pudo levantar la base de datos con Docker."
    if not _esperar(base_disponible, ESPERA_BASE, pausa):
        return "La base de datos no respondió. Revisá el archivo .env y Docker Desktop."
    return None


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.ESTILO_APP)

    cartel = QWidget()
    cartel.setWindowTitle(theme.SISTEMA)
    cartel.setWindowIcon(QIcon(theme.RUTA_ESCUDO))
    cartel.setFixedSize(420, 250)
    cartel.setStyleSheet("background-color: #ffffff;")
    layout = QVBoxLayout(cartel)
    layout.addWidget(theme.escudo(120))
    mensaje = QLabel("Iniciando...")
    mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
    mensaje.setWordWrap(True)
    layout.addWidget(mensaje)

    def avisar(texto):
        mensaje.setText(texto)
        cartel.show()
        app.processEvents()

    def pausa(segundos):
        limite = time.monotonic() + segundos
        while time.monotonic() < limite:
            app.processEvents()
            time.sleep(0.05)

    error = preparar_base(avisar, pausa)
    cartel.close()
    if error:
        QMessageBox.critical(None, theme.SISTEMA, error)
        sys.exit(1)

    from ui.login_window import LoginWindow

    window = LoginWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
