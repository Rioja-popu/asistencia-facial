from datetime import datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QFileDialog, QHBoxLayout, QHeaderView, QLabel, QVBoxLayout, QWidget

from repositories import asistencia_repository, ausencia_repository, docente_repository
from services import report_service, situacion_service
from ui import theme


class InformesView(QWidget):
    """Consulta de asistencia por docente y período, con exportación a Excel y PDF."""

    def __init__(self, nombre_usuario):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self.docentes = {}
        self.resultado = None  # (docente, desde, hasta, filas) de la última consulta

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Informes de asistencia"))
        layout.addWidget(
            theme.etiqueta(
                "Cada fila es una obligación del docente (clase, mesa o jornada) con su "
                "situación ya calculada según el horario previsto.",
                "subtitulo",
            )
        )

        filtros = QHBoxLayout()
        self.combo_docente = theme.combo([])
        hoy = QDate.currentDate()
        self.date_desde = QDateEdit(QDate(hoy.year(), hoy.month(), 1))
        self.date_hasta = QDateEdit(hoy)
        for campo in (self.date_desde, self.date_hasta):
            campo.setDisplayFormat("dd/MM/yyyy")
            campo.setCalendarPopup(True)
        filtros.addWidget(QLabel("Docente:"))
        filtros.addWidget(self.combo_docente, 3)
        filtros.addWidget(QLabel("Desde:"))
        filtros.addWidget(self.date_desde, 1)
        filtros.addWidget(QLabel("Hasta:"))
        filtros.addWidget(self.date_hasta, 1)
        filtros.addWidget(theme.boton("Consultar", al_hacer_clic=self._consultar))
        layout.addLayout(filtros)

        self.tabla = theme.crear_tabla(report_service.COLUMNAS)
        # Las columnas cortas se ajustan al texto; obligación y situación ocupan el resto
        encabezado = self.tabla.horizontalHeader()
        for columna in (0, 1, 3, 4, 5):
            encabezado.setSectionResizeMode(columna, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.tabla)

        self.lbl_resumen = theme.etiqueta("", "subtitulo")
        layout.addWidget(self.lbl_resumen)

        fila = QHBoxLayout()
        self.btn_excel = theme.boton(
            "Exportar a Excel", "confirmar", lambda: self._exportar("xlsx")
        )
        self.btn_pdf = theme.boton("Exportar a PDF", "peligro", lambda: self._exportar("pdf"))
        fila.addWidget(self.btn_excel)
        fila.addWidget(self.btn_pdf)
        fila.addStretch()
        layout.addLayout(fila)
        self._habilitar_exportacion(False)

    def _habilitar_exportacion(self, habilitar):
        self.btn_excel.setEnabled(habilitar)
        self.btn_pdf.setEnabled(habilitar)

    def refrescar(self):
        try:
            docentes = docente_repository.listar_docentes()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.docentes = {d["id"]: d for d in docentes}
        theme.recargar_combo(
            self.combo_docente,
            [
                (theme.nombre_docente(d) + ("" if d["activo"] else " (inactivo)"), d["id"])
                for d in docentes
            ],
        )
        # Los datos pudieron cambiar desde la última consulta
        self.resultado = None
        self.tabla.setRowCount(0)
        self.lbl_resumen.setText("")
        self._habilitar_exportacion(False)

    def _consultar(self):
        docente_id = self.combo_docente.currentData()
        if docente_id is None:
            theme.avisar(self, "Dato faltante", "No hay docentes registrados.")
            return
        desde = self.date_desde.date().toPython()
        hasta = self.date_hasta.date().toPython()
        if hasta < desde:
            theme.avisar(self, "Período inválido", "La fecha 'hasta' es anterior a 'desde'.")
            return
        try:
            obligaciones = asistencia_repository.obtener_obligaciones(docente_id, desde, hasta)
            ausencias = ausencia_repository.obtener_ausencias(docente_id, desde, hasta)
        except Exception as e:
            theme.error_bd(self, e)
            return
        filas = situacion_service.clasificar(obligaciones, ausencias, datetime.now())
        self.resultado = (self.docentes[docente_id], desde, hasta, filas)
        theme.llenar_tabla(self.tabla, report_service.filas_informe(filas))
        if filas:
            self.lbl_resumen.setText(
                "   |   ".join(f"{n}: {c}" for n, c in report_service.filas_totales(filas))
            )
        else:
            self.lbl_resumen.setText(report_service.MENSAJE_SIN_OBLIGACIONES)
        self._habilitar_exportacion(True)

    def _exportar(self, extension):
        if self.resultado is None:
            return
        docente, desde, hasta, filas = self.resultado
        filtro = "Excel (*.xlsx)" if extension == "xlsx" else "PDF (*.pdf)"
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe",
            report_service.nombre_archivo_sugerido(docente, desde, hasta, extension),
            filtro,
        )
        if not ruta:
            return
        if not ruta.lower().endswith("." + extension):
            ruta += "." + extension
        try:
            particulares = [
                (
                    anio,
                    ausencia_repository.contar_particulares(docente["id"], anio),
                    ausencia_repository.PARTICULARES_POR_ANIO,
                )
                for anio in range(desde.year, hasta.year + 1)
            ]
            encabezado = report_service.datos_encabezado(
                docente, desde, hasta, self.nombre_usuario, particulares
            )
            if extension == "xlsx":
                report_service.generar_excel(ruta, encabezado, filas)
            else:
                report_service.generar_pdf(ruta, encabezado, filas, theme.RUTA_ESCUDO)
        except Exception as e:
            theme.avisar(self, "No se pudo exportar", f"No se pudo generar el archivo:\n{e}")
            return
        theme.informar(self, "Informe generado", f"El informe se guardó en:\n{ruta}")
