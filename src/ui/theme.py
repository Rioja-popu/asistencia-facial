"""Identidad visual del IES N.º 7 Populorum Progressio y widgets compartidos."""

import os

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyledItemDelegate,
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

# Colores de los estados de asistencia: clave -> (fondo, texto)
COLORES_ESTADO = {
    "bien": ("#dcf2e4", "#1e6b41"),
    "atencion": ("#fdf0c8", "#8a5a00"),
    "mal": ("#f9dcd8", "#a3261a"),
    "aviso": ("#d9eefb", "#125a8c"),
    "neutro": ("#e8ecf1", "#56616e"),
}
ROL_ESTADO = Qt.ItemDataRole.UserRole + 1
ANCHO_MAXIMO_COLUMNA = 420
# Si la tabla no entra, las columnas más anchas que esto se achican hasta este ancho
ANCHO_RECORTABLE = 200

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
    QLabel#titulo {{
        font-size: 20px; font-weight: bold; color: {AZUL};
        border: none; border-bottom: 3px solid {DORADO}; padding: 0 0 5px 0;
        margin-bottom: 4px; qproperty-indent: 0;
    }}
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
    QPushButton[rol="peligro"] {{ background-color: {ROJO}; }}
    QPushButton[rol="peligro"]:hover {{ background-color: #96281b; }}
    QPushButton[rol="secundario"], QPushButton[rol="neutro"] {{
        background-color: #ffffff; padding: 6px 13px;
    }}
    QPushButton[rol="secundario"] {{ color: {AZUL_CLARO}; border: 1px solid {AZUL_CLARO}; }}
    QPushButton[rol="secundario"]:hover {{ background-color: #e3eefa; }}
    QPushButton[rol="neutro"] {{ color: #56616e; border: 1px solid #b8c2cf; }}
    QPushButton[rol="neutro"]:hover {{ background-color: #eef1f5; }}
    QPushButton:disabled, QPushButton[rol]:disabled {{
        background-color: #e4e9ef; color: #9aa5b1; border: 1px solid #d5dde8;
        padding: 6px 13px;
    }}
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


# El archivo trae el escudo en un círculo blanco sobre un cuadrado turquesa:
# margen de ese cuadrado a cada lado (fracción del ancho) y diámetro del círculo
_MARGEN_ESCUDO = (0.08, 0.09)
_DIAMETRO_ESCUDO = 0.823


def escudo(tamano):
    """El escudo recortado al círculo blanco, sin el recuadro turquesa."""
    etiqueta = QLabel()
    original = QPixmap(RUTA_ESCUDO)
    if not original.isNull():
        lado = round(original.width() * _DIAMETRO_ESCUDO)
        recorte = original.copy(
            round(original.width() * _MARGEN_ESCUDO[0]),
            round(original.height() * _MARGEN_ESCUDO[1]),
            lado, lado,
        ).scaled(
            tamano, tamano,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pixmap = QPixmap(tamano, tamano)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        contorno = QPainterPath()
        contorno.addEllipse(QRectF(1, 1, tamano - 2, tamano - 2))
        painter.setClipPath(contorno)
        painter.drawPixmap(0, 0, recorte)
        painter.end()
        etiqueta.setPixmap(pixmap)
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


class PintorEstado(QStyledItemDelegate):
    """Dibuja como etiqueta de color las celdas que tienen un estado asignado."""

    def paint(self, painter, option, index):
        estado = index.data(ROL_ESTADO)
        if estado not in COLORES_ESTADO:
            super().paint(painter, option, index)
            return
        fondo, texto = COLORES_ESTADO[estado]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(option.rect).adjusted(4, 3, -4, -3)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(area, 9, 9)
        fuente = QFont(option.font)
        fuente.setBold(True)
        painter.setFont(fuente)
        painter.setPen(QColor(texto))
        interior = area.adjusted(8, 0, -8, 0)
        contenido = painter.fontMetrics().elidedText(
            str(index.data() or ""), Qt.TextElideMode.ElideRight, int(interior.width())
        )
        alineacion = index.data(Qt.ItemDataRole.TextAlignmentRole) or int(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        painter.drawText(interior, int(alineacion), contenido)
        painter.restore()

    def sizeHint(self, option, index):
        medida = super().sizeHint(option, index)
        if index.data(ROL_ESTADO) in COLORES_ESTADO:
            # Lugar para la negrita y los bordes redondeados
            medida.setWidth(medida.width() + 12 + len(str(index.data() or "")))
        return medida


class TablaSeleccionable(QTableWidget):
    """Tabla del sistema.

    Un clic en la fila ya elegida, o fuera de las filas, la deselecciona. Las
    columnas toman el ancho de su contenido y se reparten el espacio que sobra;
    si no entran, se acortan las de texto largo (el texto completo queda en la
    ayuda de la celda) y recién después aparece la barra horizontal.
    Si no hay filas, muestra un mensaje en lugar de quedar en blanco.
    """

    mensaje_vacio = "No hay datos para mostrar."

    def mousePressEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item is None or item.isSelected():
            self.clearSelection()
            return
        super().mousePressEvent(event)

    def fijar_mensaje_vacio(self, texto):
        self.mensaje_vacio = texto
        self.viewport().update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.rowCount() == 0 and self.mensaje_vacio:
            painter = QPainter(self.viewport())
            painter.setPen(QColor(GRIS))
            painter.drawText(
                self.viewport().rect().adjusted(20, 10, -20, -10),
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
                self.mensaje_vacio,
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ajustar_columnas()

    def ajustar_columnas(self):
        encabezado = self.horizontalHeader()
        anchos = [
            min(
                max(self.sizeHintForColumn(c), encabezado.sectionSizeHint(c)) + 8,
                ANCHO_MAXIMO_COLUMNA,
            )
            for c in range(self.columnCount())
        ]
        sobra = self.viewport().width() - sum(anchos)
        while sobra < 0 and max(anchos, default=0) > ANCHO_RECORTABLE:
            mayor = anchos.index(max(anchos))
            recorte = min(-sobra, anchos[mayor] - ANCHO_RECORTABLE, 20)
            anchos[mayor] -= recorte
            sobra += recorte
        total = sum(anchos)
        if sobra < 0 and -sobra <= total * 0.08:
            # Falta muy poco: se ajustan todas un poco antes que mostrar la barra
            anchos = [a * (total + sobra) // total for a in anchos]
            sobra = 0
        if sobra > 0 and anchos:
            # El espacio libre se reparte según el ancho que ya necesita cada columna
            total = sum(anchos)
            extras = [sobra * a // total for a in anchos]
            extras[-1] += sobra - sum(extras)
            anchos = [a + e for a, e in zip(anchos, extras)]
        for columna, ancho in enumerate(anchos):
            self.setColumnWidth(columna, ancho)


def crear_tabla(columnas, mensaje_vacio=None):
    tabla = TablaSeleccionable(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    tabla.setAlternatingRowColors(True)
    tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    tabla.verticalHeader().setVisible(False)
    tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    tabla.setItemDelegate(PintorEstado(tabla))
    if mensaje_vacio:
        tabla.mensaje_vacio = mensaje_vacio
    return tabla


def llenar_tabla(tabla, filas, ids=None, estados=None):
    """filas: lista de listas de texto. ids: valor asociado a cada fila.

    estados: {(fila, columna): clave de COLORES_ESTADO} para las celdas con color.
    """
    estados = estados or {}
    tabla.clearSelection()
    tabla.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            texto = "" if valor is None else str(valor)
            item = QTableWidgetItem(texto)
            item.setToolTip(texto)
            if ids is not None:
                item.setData(Qt.ItemDataRole.UserRole, ids[i])
            if (i, j) in estados:
                item.setData(ROL_ESTADO, estados[(i, j)])
            tabla.setItem(i, j, item)
    tabla.ajustar_columnas()


def resaltar_fila(tabla, fila):
    """Pone en negrita una fila, por ejemplo la de totales."""
    for columna in range(tabla.columnCount()):
        item = tabla.item(fila, columna)
        fuente = item.font()
        fuente.setBold(True)
        item.setFont(fuente)


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
