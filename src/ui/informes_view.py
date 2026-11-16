from datetime import datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from repositories import asistencia_repository, ausencia_repository, docente_repository
from services import report_service, situacion_service
from ui import theme
from ui.corregir_marcacion_dialog import CorregirMarcacionDialog

TODOS = "todos"


class InformesView(QWidget):
    """Asistencia por docente o resumen de todos, con exportación a Excel y PDF."""

    def __init__(self, usuario_id, nombre_usuario):
        super().__init__()
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.docentes = {}
        # Última consulta: (docente, desde, hasta, filas); docente es None en el resumen general
        self.resultado = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Informes de asistencia"))
        layout.addWidget(
            theme.etiqueta(
                "Cada fila es una obligación del docente (clase, mesa o jornada) con su "
                "situación ya calculada según el horario previsto. \"Todos los docentes\" "
                "muestra un resumen general del período.",
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
        self.tabla_general = theme.crear_tabla(report_service.COLUMNAS_GENERAL)
        self.tabla_general.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_general.horizontalHeader().setStretchLastSection(True)
        self.tablas = QStackedWidget()
        self.tablas.addWidget(self.tabla)
        self.tablas.addWidget(self.tabla_general)
        layout.addWidget(self.tablas)

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
        self.btn_corregir = theme.boton("Corregir marcación", "secundario", self._corregir)
        fila.addWidget(self.btn_corregir)
        layout.addLayout(fila)
        self._habilitar_exportacion(False)

    def _habilitar_exportacion(self, habilitar):
        self.btn_excel.setEnabled(habilitar)
        self.btn_pdf.setEnabled(habilitar)
        self.btn_corregir.setEnabled(
            habilitar and self.resultado is not None and self.resultado[0] is not None
        )

    def refrescar(self):
        try:
            docentes = docente_repository.listar_docentes()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.docentes = {d["id"]: d for d in docentes}
        theme.recargar_combo(
            self.combo_docente,
            [("Todos los docentes (resumen general)", TODOS)]
            + [
                (theme.nombre_docente(d) + ("" if d["activo"] else " (inactivo)"), d["id"])
                for d in docentes
            ],
        )
        # Los datos pudieron cambiar desde la última consulta
        self.resultado = None
        self.tabla.setRowCount(0)
        self.tabla_general.setRowCount(0)
        self.lbl_resumen.setText("")
        self._habilitar_exportacion(False)

    def _consultar(self):
        docente_id = self.combo_docente.currentData()
        if not self.docentes:
            theme.avisar(self, "Dato faltante", "No hay docentes registrados.")
            return
        desde = self.date_desde.date().toPython()
        hasta = self.date_hasta.date().toPython()
        if hasta < desde:
            theme.avisar(self, "Período inválido", "La fecha 'hasta' es anterior a 'desde'.")
            return
        if docente_id == TODOS:
            self._consultar_general(desde, hasta)
            return
        try:
            filas = self._filas_docente(docente_id, desde, hasta)
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.resultado = (self.docentes[docente_id], desde, hasta, filas)
        self.tablas.setCurrentWidget(self.tabla)
        theme.llenar_tabla(
            self.tabla, report_service.filas_informe(filas), list(range(len(filas)))
        )
        if filas:
            self.lbl_resumen.setText(
                "   |   ".join(f"{n}: {c}" for n, c in report_service.filas_totales(filas))
            )
        else:
            self.lbl_resumen.setText(report_service.MENSAJE_SIN_OBLIGACIONES)
        self._habilitar_exportacion(True)

    def _filas_docente(self, docente_id, desde, hasta):
        obligaciones = asistencia_repository.obtener_obligaciones(docente_id, desde, hasta)
        ausencias = ausencia_repository.obtener_ausencias(docente_id, desde, hasta)
        return situacion_service.clasificar(obligaciones, ausencias, datetime.now())

    def _consultar_general(self, desde, hasta):
        try:
            resumenes = [
                (
                    docente,
                    self._filas_docente(docente["id"], desde, hasta),
                    f"{ausencia_repository.contar_particulares(docente['id'], hasta.year)}"
                    f" de {ausencia_repository.PARTICULARES_POR_ANIO}",
                )
                for docente in self.docentes.values()
            ]
        except Exception as e:
            theme.error_bd(self, e)
            return
        filas = report_service.filas_general(resumenes)
        self.resultado = (None, desde, hasta, filas)
        self.tablas.setCurrentWidget(self.tabla_general)
        theme.llenar_tabla(
            self.tabla_general,
            filas + [report_service.fila_totales_general(filas)] if filas else [],
        )
        if filas:
            self.lbl_resumen.setText(
                f"Docentes con obligaciones en el período: {len(filas)}. "
                f"Los particulares son los usados en {hasta.year}."
            )
        else:
            self.lbl_resumen.setText(report_service.MENSAJE_SIN_DOCENTES)
        self._habilitar_exportacion(True)

    def _corregir(self):
        docente, desde, hasta, filas = self.resultado
        indice = theme.id_seleccionado(self.tabla)
        if indice is None:
            theme.avisar(self, "Sin selección", "Seleccioná una obligación de la lista.")
            return
        fila = filas[indice]
        if situacion_service.SIN_CLASES in fila["etiquetas"]:
            theme.avisar(
                self, "No corresponde",
                "Ese día es feriado o receso. Si hubo clase igual, primero quitalo "
                "de Feriados y recesos.",
            )
            return
        if datetime.combine(fila["fecha"], fila["inicio"]) > datetime.now():
            theme.avisar(self, "No corresponde", "Esa obligación todavía no empezó.")
            return
        dialogo = CorregirMarcacionDialog(docente, fila, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            asistencia_repository.corregir_marcacion(
                docente["id"], fila, dialogo.correccion, dialogo.motivo,
                self.usuario_id, datetime.now(),
            )
        except Exception as e:
            theme.error_bd(self, e)
            return
        self._consultar()

    def _exportar_general(self, extension, desde, hasta, filas):
        filtro = "Excel (*.xlsx)" if extension == "xlsx" else "PDF (*.pdf)"
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar informe",
            f"resumen_asistencia_{desde:%Y-%m-%d}_a_{hasta:%Y-%m-%d}.{extension}", filtro,
        )
        if not ruta:
            return
        if not ruta.lower().endswith("." + extension):
            ruta += "." + extension
        encabezado = report_service.encabezado_general(desde, hasta, self.nombre_usuario)
        try:
            if extension == "xlsx":
                report_service.generar_excel_general(ruta, encabezado, filas)
            else:
                report_service.generar_pdf_general(ruta, encabezado, filas, theme.RUTA_ESCUDO)
        except Exception as e:
            theme.avisar(self, "No se pudo exportar", f"No se pudo generar el archivo:\n{e}")
            return
        theme.informar(self, "Informe generado", f"El informe se guardó en:\n{ruta}")

    def _exportar(self, extension):
        if self.resultado is None:
            return
        docente, desde, hasta, filas = self.resultado
        if docente is None:
            self._exportar_general(extension, desde, hasta, filas)
            return
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
