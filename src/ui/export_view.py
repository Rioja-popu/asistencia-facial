import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from database.queries import (
    obtener_asistencias_jornada,
    obtener_jornada_de_usuario,
    obtener_jornadas_usuario,
)
from services.report_service import generar_excel, generar_pdf, nombre_sugerido

FORMATOS = {
    "xlsx": ("Excel", "Archivo Excel (*.xlsx)", generar_excel, "#27ae60", "#219150"),
    "pdf": ("PDF", "Documento PDF (*.pdf)", generar_pdf, "#e74c3c", "#c0392b"),
}


class ExportReportsView(QWidget):

    def __init__(self, usuario_id):
        super().__init__()
        self.usuario_id = usuario_id
        self.ultima_carpeta = os.path.expanduser("~")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)

        title_label = QLabel("📄 Exportar Informes")
        title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 15px;"
        )
        main_layout.addWidget(title_label)

        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        main_layout.addWidget(self.lbl_estado)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Cátedra", "Horario", "Excel", "PDF"]
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabla.setAlternatingRowColors(True)
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet(
            """
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f4f6f7;
                color: #2c3e50;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ffffff;
                font-weight: bold;
                padding: 6px 10px;
                border: none;
            }
        """
        )
        main_layout.addWidget(self.tabla)

    def refrescar(self):
        """Vuelve a consultar en PostgreSQL las Jornadas del usuario autenticado."""
        self.tabla.setRowCount(0)
        try:
            jornadas = obtener_jornadas_usuario(self.usuario_id)
        except Exception as e:
            self.lbl_estado.setText("No se pudieron cargar las Jornadas.")
            QMessageBox.critical(
                self,
                "Error de base de datos",
                f"No se pudieron cargar las Jornadas: {e}",
            )
            return

        if jornadas:
            self.lbl_estado.setText("Jornadas registradas:")
        else:
            self.lbl_estado.setText("Todavía no registraste ninguna Jornada.")

        self.tabla.setRowCount(len(jornadas))
        for fila, (jornada_id, fecha, catedra, entrada, salida) in enumerate(jornadas):
            textos = (
                fecha.strftime("%d/%m/%Y"),
                catedra,
                f"{entrada.strftime('%H:%M')} - {salida.strftime('%H:%M')}",
            )
            for columna, texto in enumerate(textos):
                item = QTableWidgetItem(texto)
                if columna != 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, columna, item)

            for columna, formato in ((3, "xlsx"), (4, "pdf")):
                self.tabla.setCellWidget(
                    fila, columna, self._crear_boton(jornada_id, formato)
                )
        self.tabla.resizeRowsToContents()

    def _crear_boton(self, jornada_id, formato):
        texto, _, _, color, color_hover = FORMATOS[formato]
        boton = QPushButton(texto)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                padding: 5px 14px;
                margin: 3px 6px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {color_hover}; }}
        """
        )
        boton.clicked.connect(lambda: self._exportar(jornada_id, formato))
        return boton

    def _exportar(self, jornada_id, formato):
        _, filtro, generar, _, _ = FORMATOS[formato]

        try:
            jornada = obtener_jornada_de_usuario(jornada_id, self.usuario_id)
        except Exception as e:
            QMessageBox.critical(
                self, "Error de base de datos", f"No se pudo consultar la Jornada: {e}"
            )
            return
        if jornada is None:
            QMessageBox.warning(
                self,
                "Jornada no disponible",
                "La Jornada no existe o no pertenece al usuario autenticado.",
            )
            self.refrescar()
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar como...",
            os.path.join(self.ultima_carpeta, nombre_sugerido(jornada, formato)),
            filtro,
        )
        if not ruta:
            return
        if not ruta.lower().endswith("." + formato):
            ruta += "." + formato
        self.ultima_carpeta = os.path.dirname(ruta)

        try:
            # Se consulta después del diálogo para reflejar el estado actual en PostgreSQL
            jornada = obtener_jornada_de_usuario(jornada_id, self.usuario_id)
            if jornada is None:
                raise PermissionError(
                    "La Jornada no existe o no pertenece al usuario autenticado."
                )
            asistencias = obtener_asistencias_jornada(jornada_id, self.usuario_id)
            generar(ruta, jornada, asistencias)
        except Exception as e:
            QMessageBox.critical(
                self, "Error al exportar", f"No se pudo generar el informe: {e}"
            )
            return

        QMessageBox.information(
            self,
            "Informe generado",
            f"El archivo fue creado correctamente:\n{ruta}",
        )
