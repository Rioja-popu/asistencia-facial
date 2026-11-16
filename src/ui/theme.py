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

# Qt necesita las rutas de la hoja de estilo con barras "/"
_ICONOS = os.path.normpath(os.path.join(os.path.dirname(RUTA_ESCUDO), "iconos")).replace(
    os.sep, "/"
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
    QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {AZUL_CLARO};
    }}
    /* Lista desplegable con barra de desplazamiento en lugar del menú nativo */
    QComboBox {{ combobox-popup: 0; padding-right: 30px; }}
    QDateEdit {{ padding-right: 30px; }}
    QComboBox QAbstractItemView {{
        background-color: #ffffff; color: {TEXTO}; outline: none;
        border: 1px solid {AZUL_CLARO};
        selection-background-color: {AZUL_CLARO}; selection-color: #ffffff;
    }}
    QComboBox QAbstractItemView::item {{ min-height: 26px; padding-left: 6px; }}
    QComboBox::drop-down, QDateEdit::drop-down {{
        subcontrol-origin: border; subcontrol-position: center right;
        width: 28px; border: none; background-color: {AZUL_CLARO};
        border-top-right-radius: 4px; border-bottom-right-radius: 4px;
    }}
    QComboBox::drop-down:hover, QDateEdit::drop-down:hover {{ background-color: {AZUL}; }}
    QComboBox::drop-down:disabled, QDateEdit::drop-down:disabled {{ background-color: #c5ced9; }}
    QComboBox::down-arrow, QDateEdit::down-arrow {{
        image: url({_ICONOS}/flecha_abajo.png); width: 14px; height: 14px;
    }}
    QTimeEdit, QSpinBox {{ padding-right: 28px; }}
    QTimeEdit::up-button, QSpinBox::up-button {{
        subcontrol-origin: border; subcontrol-position: top right;
        width: 24px; border: none; background-color: {AZUL_CLARO};
        border-top-right-radius: 4px;
    }}
    QTimeEdit::down-button, QSpinBox::down-button {{
        subcontrol-origin: border; subcontrol-position: bottom right;
        width: 24px; border: none; background-color: {AZUL_CLARO};
        border-top: 1px solid #ffffff; border-bottom-right-radius: 4px;
    }}
    QTimeEdit::up-button:hover, QSpinBox::up-button:hover,
    QTimeEdit::down-button:hover, QSpinBox::down-button:hover {{ background-color: {AZUL}; }}
    QTimeEdit::up-button:disabled, QSpinBox::up-button:disabled,
    QTimeEdit::down-button:disabled, QSpinBox::down-button:disabled {{
        background-color: #c5ced9;
    }}
    QTimeEdit::up-arrow, QSpinBox::up-arrow {{
        image: url({_ICONOS}/flecha_arriba.png); width: 10px; height: 10px;
    }}
    QTimeEdit::down-arrow, QSpinBox::down-arrow {{
        image: url({_ICONOS}/flecha_abajo.png); width: 10px; height: 10px;
    }}
    QScrollBar:vertical {{
        background-color: #e8eef5; width: 12px; margin: 0; border: none;
    }}
    QScrollBar:horizontal {{
        background-color: #e8eef5; height: 12px; margin: 0; border: none;
    }}
    QScrollBar::handle {{ background-color: {AZUL_CLARO}; border-radius: 5px; margin: 2px; }}
    QScrollBar::handle:vertical {{ min-height: 30px; }}
    QScrollBar::handle:horizontal {{ min-width: 30px; }}
    QScrollBar::handle:hover {{ background-color: {AZUL}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
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
    QTableWidget::item:selected {{ background-color: #cfe3f7; color: {TEXTO}; }}
    QHeaderView::section {{
        background-color: {AZUL}; color: #ffffff; font-weight: bold;
        padding: 6px; border: none;
    }}
    QFrame#tarjeta {{
        background-color: #ffffff; border: 1px solid #d5dde8; border-radius: 8px;
    }}
    QCalendarWidget QWidget {{ background-color: #ffffff; color: {TEXTO}; }}
    QCalendarWidget QWidget#qt_calendar_navigationbar {{ background-color: {AZUL}; }}
    QCalendarWidget QToolButton {{
        background-color: {AZUL}; color: #ffffff; font-weight: bold;
        border: none; padding: 4px 8px;
    }}
    QCalendarWidget QToolButton:hover {{ background-color: {AZUL_CLARO}; }}
    QCalendarWidget QToolButton::menu-indicator {{ image: none; }}
    QCalendarWidget QSpinBox {{ background-color: #ffffff; color: {TEXTO}; padding-right: 22px; }}
    QCalendarWidget QMenu {{ background-color: #ffffff; color: {TEXTO}; }}
    QCalendarWidget QMenu::item:selected {{ background-color: {AZUL_CLARO}; color: #ffffff; }}
    QCalendarWidget QAbstractItemView {{
        background-color: #ffffff; alternate-background-color: #eef3f9;
        color: {TEXTO}; outline: none;
        selection-background-color: {AZUL_CLARO}; selection-color: #ffffff;
    }}
    QCalendarWidget QAbstractItemView:disabled {{ color: #b3bcc8; }}
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


class TablaSeleccionable(QTableWidget):
    """Tabla en la que un clic en la fila ya elegida, o fuera de las filas, la deselecciona."""

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is None or item.isSelected():
            self.clearSelection()
            return
        super().mousePressEvent(event)


def crear_tabla(columnas):
    tabla = TablaSeleccionable(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    return tabla


def llenar_tabla(tabla, filas, ids=None):
    """filas: lista de listas de texto. ids: valor asociado a cada fila."""
    tabla.clearSelection()
    tabla.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            item = QTableWidgetItem("" if valor is None else str(valor))
            if ids is not None:
                item.setData(Qt.ItemDataRole.UserRole, ids[i])
            tabla.setItem(i, j, item)


def id_seleccionado(tabla):
    filas = tabla.selectionModel().selectedRows()
    if not filas:
        return None
    return tabla.item(filas[0].row(), 0).data(Qt.ItemDataRole.UserRole)


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
