"""Identidad visual del IES N.º 7 Populorum Progressio y widgets compartidos."""

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

INSTITUCION = "IES N.º 7 Populorum Progressio"
SISTEMA = "Asistencia Docente"

# Colores tomados del escudo y del sitio institucional
AZUL = "#143560"
AZUL_CLARO = "#1e73be"
TURQUESA = "#0197b2"
DORADO = "#f3d076"
FONDO = "#f4f7fb"
TEXTO = "#1f2d3d"
GRIS = "#6b7785"
VERDE = "#2e8b57"
ROJO = "#c0392b"

RUTA_ESCUDO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "escudo.png"
)

DIAS_SEMANA = {
    1: "Lunes", 2: "Martes", 3: "Miércoles", 4: "Jueves",
    5: "Viernes", 6: "Sábado", 7: "Domingo",
}

ESTILO_APP = f"""
    QWidget {{ color: {TEXTO}; font-size: 13px; }}
    QLabel#titulo {{ font-size: 20px; font-weight: bold; color: {AZUL}; }}
    QLabel#subtitulo {{ font-size: 13px; color: {GRIS}; }}
    QLabel#seccion {{ font-size: 14px; font-weight: bold; color: {AZUL}; }}
    QLineEdit, QDateEdit, QTimeEdit, QSpinBox, QComboBox {{
        padding: 5px; border: 1px solid #c5ced9; border-radius: 4px;
        background-color: #ffffff; color: {TEXTO};
    }}
    QComboBox QAbstractItemView {{
        background-color: #ffffff; color: {TEXTO};
        selection-background-color: {AZUL_CLARO}; selection-color: #ffffff;
    }}
    QPushButton {{
        background-color: {AZUL_CLARO}; color: #ffffff; font-weight: bold;
        padding: 7px 14px; border: none; border-radius: 4px;
    }}
    QPushButton:hover {{ background-color: {AZUL}; }}
    QPushButton:disabled {{ background-color: #c5ced9; color: #7b8794; }}
    QPushButton[rol="confirmar"] {{ background-color: {VERDE}; }}
    QPushButton[rol="peligro"] {{ background-color: {ROJO}; }}
    QPushButton[rol="secundario"] {{ background-color: {TURQUESA}; }}
    QTableWidget {{
        background-color: #ffffff; alternate-background-color: #eef3f9;
        border: 1px solid #d5dde8; gridline-color: #e3e9f1;
    }}
    QHeaderView::section {{
        background-color: {AZUL}; color: #ffffff; font-weight: bold;
        padding: 6px; border: none;
    }}
    QFrame#tarjeta {{
        background-color: #ffffff; border: 1px solid #d5dde8; border-radius: 8px;
    }}
    QMessageBox, QDialog {{ background-color: #ffffff; }}
    QMessageBox QPushButton {{ min-width: 80px; }}
"""


def escudo(tamano):
    etiqueta = QLabel()
    pixmap = QPixmap(RUTA_ESCUDO)
    if not pixmap.isNull():
        etiqueta.setPixmap(
            pixmap.scaled(
                tamano, tamano,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return etiqueta


def etiqueta(texto, nombre="titulo"):
    widget = QLabel(texto)
    widget.setObjectName(nombre)
    widget.setWordWrap(True)
    return widget


def boton(texto, rol=None, al_hacer_clic=None):
    widget = QPushButton(texto)
    if rol:
        widget.setProperty("rol", rol)
    if al_hacer_clic:
        widget.clicked.connect(al_hacer_clic)
    return widget


def crear_tabla(columnas):
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return tabla


def llenar_tabla(tabla, filas, ids=None):
    """filas: lista de listas de texto. ids: valor asociado a cada fila."""
    tabla.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            item = QTableWidgetItem("" if valor is None else str(valor))
            if ids is not None:
                item.setData(Qt.ItemDataRole.UserRole, ids[i])
            tabla.setItem(i, j, item)


def id_seleccionado(tabla):
    fila = tabla.currentRow()
    if fila < 0:
        return None
    return tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)


def combo(opciones):
    """opciones: [(texto, valor), ...]"""
    widget = QComboBox()
    for texto, valor in opciones:
        widget.addItem(texto, valor)
    return widget


def recargar_combo(widget, opciones):
    actual = widget.currentData()
    widget.blockSignals(True)
    widget.clear()
    for texto, valor in opciones:
        widget.addItem(texto, valor)
    indice = widget.findData(actual)
    widget.setCurrentIndex(indice if indice >= 0 else 0)
    widget.blockSignals(False)


def nombre_docente(docente):
    return f"{docente['apellido']}, {docente['nombre']}"


def hora(valor):
    return valor.strftime("%H:%M") if valor else ""


def fecha(valor):
    return valor.strftime("%d/%m/%Y") if valor else ""


def avisar(padre, titulo, texto):
    QMessageBox.warning(padre, titulo, texto)


def informar(padre, titulo, texto):
    QMessageBox.information(padre, titulo, texto)


def error_bd(padre, excepcion):
    QMessageBox.critical(
        padre, "Error de base de datos", f"No se pudo completar la operación:\n{excepcion}"
    )


def confirmar(padre, titulo, texto):
    return (
        QMessageBox.question(
            padre, titulo, texto,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        == QMessageBox.StandardButton.Yes
    )
