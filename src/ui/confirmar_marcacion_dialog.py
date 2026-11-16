from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout

from services import marcacion_service
from ui import iconos, theme

LADO_FOTO = 132


def _etiqueta_estado(texto, estado):
    fondo, color = theme.COLORES_ESTADO[estado]
    etiqueta = QLabel(texto)
    etiqueta.setStyleSheet(
        f"background-color: {fondo}; color: {color}; font-weight: bold;"
        "padding: 3px 10px; border-radius: 9px;"
    )
    return etiqueta


def _foto_redondeada(imagen):
    """Recorta la foto a un cuadrado de esquinas redondeadas; sin foto, una silueta."""
    lienzo = QPixmap(LADO_FOTO, LADO_FOTO)
    lienzo.fill(Qt.GlobalColor.transparent)
    painter = QPainter(lienzo)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    contorno = QPainterPath()
    contorno.addRoundedRect(QRectF(0, 0, LADO_FOTO, LADO_FOTO), 12, 12)
    painter.setClipPath(contorno)
    foto = QPixmap()
    if imagen and foto.loadFromData(imagen):
        foto = foto.scaled(
            LADO_FOTO, LADO_FOTO,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            (LADO_FOTO - foto.width()) // 2, (LADO_FOTO - foto.height()) // 2, foto
        )
    else:
        painter.fillRect(lienzo.rect(), theme.FONDO)
        silueta = iconos.pixmap("docentes", theme.GRIS, 80, 1.0)
        painter.drawPixmap((LADO_FOTO - 80) // 2, (LADO_FOTO - 80) // 2, silueta)
    painter.end()
    return lienzo


class ConfirmarMarcacionDialog(QDialog):
    """Muestra a quién se reconoció y qué se va a registrar. Sólo guarda con OK."""

    def __init__(self, nombre, foto, propuesta, ahora, tiene_ausencia, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirmar marcación")
        self.setMinimumWidth(520)
        es_entrada = propuesta["operacion"] == marcacion_service.ENTRADA

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(18)
        lbl_foto = QLabel()
        lbl_foto.setPixmap(_foto_redondeada(foto))
        lbl_foto.setFixedSize(LADO_FOTO, LADO_FOTO)
        cabecera.addWidget(lbl_foto)
        datos = QVBoxLayout()
        datos.setSpacing(4)
        datos.addStretch()
        datos.addWidget(theme.etiqueta("Docente reconocido", "subtitulo"))
        lbl_nombre = QLabel(nombre)
        lbl_nombre.setWordWrap(True)
        lbl_nombre.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {theme.AZUL};")
        datos.addWidget(lbl_nombre)
        datos.addSpacing(6)
        operacion = QLabel(f"{'ENTRADA' if es_entrada else 'SALIDA'}   {ahora:%H:%M}")
        operacion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        operacion.setStyleSheet(
            f"background-color: {theme.VERDE if es_entrada else theme.AZUL_CLARO};"
            "color: #ffffff; font-size: 20px; font-weight: bold;"
            "padding: 8px 16px; border-radius: 6px;"
        )
        datos.addWidget(operacion)
        datos.addStretch()
        cabecera.addLayout(datos, 1)
        layout.addLayout(cabecera)

        layout.addWidget(
            theme.etiqueta(
                "Se registra la entrada de:" if es_entrada else "Se registra la salida de:",
                "seccion",
            )
        )
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        obligaciones = QVBoxLayout(tarjeta)
        obligaciones.setContentsMargins(12, 8, 12, 8)
        for item in propuesta["items"]:
            fila = QHBoxLayout()
            texto = QLabel(
                f"{item['descripcion']}\n"
                f"{theme.hora(item['inicio'])} a {theme.hora(item['fin'])}"
            )
            texto.setWordWrap(True)
            fila.addWidget(texto, 1)
            if es_entrada:
                tarde = item.get("tardanza")
                estado = _etiqueta_estado(
                    "Tardanza" if tarde else "En horario", "atencion" if tarde else "bien"
                )
                fila.addWidget(estado, alignment=Qt.AlignmentFlag.AlignVCenter)
            elif item.get("salida_anticipada"):
                fila.addWidget(
                    _etiqueta_estado("Salida anticipada", "atencion"),
                    alignment=Qt.AlignmentFlag.AlignVCenter,
                )
            obligaciones.addLayout(fila)
        layout.addWidget(tarjeta)

        if tiene_ausencia:
            aviso = _etiqueta_estado("Atención: tenés una ausencia cargada para hoy.", "mal")
            aviso.setWordWrap(True)
            layout.addWidget(aviso)

        layout.addWidget(QLabel("¿Confirmás la marcación?"))
        botones = QHBoxLayout()
        botones.addStretch()
        self.btn_cancelar = theme.boton("Cancelar", "peligro", self.reject)
        self.btn_ok = theme.boton("OK", "confirmar", self.accept)
        for boton in (self.btn_cancelar, self.btn_ok):
            boton.setMinimumWidth(110)
            botones.addWidget(boton)
        self.btn_ok.setDefault(True)
        layout.addLayout(botones)
