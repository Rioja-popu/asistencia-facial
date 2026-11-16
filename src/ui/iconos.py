"""Iconos de línea del menú, dibujados con Qt para no depender de archivos de imagen."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

# Los dibujos están pensados sobre una grilla de 24 x 24
_GRILLA = 24


def _linea(*puntos):
    camino = QPainterPath(QPointF(*puntos[0]))
    for punto in puntos[1:]:
        camino.lineTo(*punto)
    return camino


def _circulo(x, y, radio):
    camino = QPainterPath()
    camino.addEllipse(QPointF(x, y), radio, radio)
    return camino


def _rectangulo(x, y, ancho, alto, radio=2):
    camino = QPainterPath()
    camino.addRoundedRect(QRectF(x, y, ancho, alto), radio, radio)
    return camino


def _curva(inicio, control_1, control_2, fin):
    camino = QPainterPath(QPointF(*inicio))
    camino.cubicTo(QPointF(*control_1), QPointF(*control_2), QPointF(*fin))
    return camino


def _estrella():
    camino = QPainterPath()
    camino.addPolygon(
        QPolygonF(
            [
                QPointF(12, 3), QPointF(14.6, 9), QPointF(21, 9.6), QPointF(16.2, 13.9),
                QPointF(17.6, 20.2), QPointF(12, 16.9), QPointF(6.4, 20.2),
                QPointF(7.8, 13.9), QPointF(3, 9.6), QPointF(9.4, 9),
            ]
        )
    )
    camino.closeSubpath()
    return camino


_DIBUJOS = {
    "inicio": lambda: [
        _linea((3, 11.5), (12, 3.5), (21, 11.5)),
        _linea((5.5, 9.5), (5.5, 20), (18.5, 20), (18.5, 9.5)),
        _linea((10, 20), (10, 14), (14, 14), (14, 20)),
    ],
    "marcacion": lambda: [
        _rectangulo(3, 7, 18, 13),
        _circulo(12, 13.5, 3.5),
        _linea((9, 7), (10, 4.5), (14, 4.5), (15, 7)),
    ],
    "docentes": lambda: [
        _circulo(12, 8, 3.8),
        _curva((4.5, 20.5), (4.5, 13.5), (19.5, 13.5), (19.5, 20.5)),
    ],
    "catedras": lambda: [
        _linea((12, 6.5), (12, 20)),
        _curva((12, 6.5), (9, 4), (5.5, 4), (3, 5)),
        _linea((3, 5), (3, 18.5)),
        _curva((3, 18.5), (5.5, 17.5), (9, 17.5), (12, 20)),
        _curva((12, 6.5), (15, 4), (18.5, 4), (21, 5)),
        _linea((21, 5), (21, 18.5)),
        _curva((21, 18.5), (18.5, 17.5), (15, 17.5), (12, 20)),
    ],
    "horarios": lambda: [_circulo(12, 12, 8.5), _linea((12, 7), (12, 12), (15.5, 14))],
    "actividades": lambda: [_estrella()],
    "ausencias": lambda: [
        _rectangulo(5, 3.5, 14, 17.5),
        _linea((9, 9.5), (15, 15.5)),
        _linea((15, 9.5), (9, 15.5)),
    ],
    "feriados": lambda: [
        _rectangulo(3.5, 5.5, 17, 15),
        _linea((3.5, 10.5), (20.5, 10.5)),
        _linea((8, 3.5), (8, 7)),
        _linea((16, 3.5), (16, 7)),
    ],
    "usuarios": lambda: [
        _circulo(9, 8.5, 3.3),
        _curva((2.5, 20), (2.5, 13.5), (15.5, 13.5), (15.5, 20)),
        _circulo(17, 9.5, 2.6),
        _curva((17.5, 14.5), (20.5, 14.5), (21.5, 17), (21.5, 20)),
    ],
    "llave": lambda: [
        _circulo(8, 15.5, 4),
        _linea((11, 12.5), (20, 3.5)),
        _linea((16.5, 7), (19.5, 10)),
    ],
    "salir": lambda: [
        _linea((10, 4), (4.5, 4), (4.5, 20), (10, 20)),
        _linea((10, 12), (20, 12)),
        _linea((16, 8), (20, 12), (16, 16)),
    ],
    "informes": lambda: [
        _linea((3, 20.5), (21, 20.5)),
        _linea((7, 20), (7, 13)),
        _linea((12, 20), (12, 5.5)),
        _linea((17, 20), (17, 10)),
    ],
}


def pixmap(nombre, color="#ffffff", tamano=20, escala=2.0):
    """Dibujo del icono; `escala` lo deja nítido en pantallas de alta densidad."""
    lado = round(tamano * escala)
    imagen = QPixmap(lado, lado)
    imagen.fill(Qt.GlobalColor.transparent)
    painter = QPainter(imagen)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(lado / _GRILLA, lado / _GRILLA)
    lapiz = QPen(QColor(color))
    lapiz.setWidthF(1.8)
    lapiz.setCapStyle(Qt.PenCapStyle.RoundCap)
    lapiz.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(lapiz)
    for camino in _DIBUJOS[nombre]():
        painter.drawPath(camino)
    painter.end()
    imagen.setDevicePixelRatio(escala)
    return imagen


def icono(nombre, color="#ffffff"):
    return QIcon(pixmap(nombre, color))
