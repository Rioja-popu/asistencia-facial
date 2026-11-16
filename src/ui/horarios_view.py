from datetime import date, datetime, timedelta

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from repositories import academico_repository as repo
from repositories import docente_repository
from services import importacion_service
from services.importacion_service import MINUTOS_CLASE, MINUTOS_MODULO
from ui import theme
from ui.importar_horarios_dialog import ImportarHorariosDialog



class HorariosView(QWidget):
    """Días y horarios en los que cada docente dicta cada cátedra."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Horarios de cátedra"))
        layout.addWidget(
            theme.etiqueta(
                "Los horarios se arman en módulos de 40 min, con un mínimo de una clase "
                "(1 h 20 min). Los módulos seguidos de la misma cátedra van en un solo bloque.",
                "subtitulo",
            )
        )

        self.combo_docente = theme.combo([])
        self.combo_docente.currentIndexChanged.connect(self._cargar_horarios)
        layout.addWidget(self.combo_docente)

        self.tabla = theme.crear_tabla(
            ["Día", "Horario", "Cátedra", "Carrera", "Vigente desde", "Vigente hasta"]
        )
        layout.addWidget(self.tabla)

        fila = QHBoxLayout()
        fila.addWidget(
            theme.boton("Dar de baja desde hoy", "secundario", self._finalizar)
        )
        fila.addWidget(theme.boton("Eliminar (cargado por error)", "peligro", self._eliminar))
        fila.addStretch()
        fila.addWidget(
            theme.boton("Descargar planilla modelo", "secundario", self._descargar_planilla)
        )
        fila.addWidget(theme.boton("Importar desde Excel", "secundario", self._importar))
        layout.addLayout(fila)

        layout.addWidget(theme.etiqueta("Agregar horario", "seccion"))
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        form = QFormLayout(tarjeta)
        self.combo_catedra = theme.combo([])
        self.combo_dia = theme.combo([(n, d) for d, n in theme.DIAS_SEMANA.items()])
        self.time_inicio = QTimeEdit(QTime(8, 0))
        self.time_inicio.setDisplayFormat("HH:mm")
        self.spin_clases = QSpinBox()
        self.spin_clases.setRange(MINUTOS_CLASE // MINUTOS_MODULO, 8)
        self.lbl_fin = theme.etiqueta("", "subtitulo")
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setCalendarPopup(True)
        form.addRow("Cátedra:", self.combo_catedra)
        form.addRow("Día:", self.combo_dia)
        form.addRow("Hora de inicio:", self.time_inicio)
        form.addRow("Módulos de 40 min seguidos:", self.spin_clases)
        form.addRow("Hora de fin:", self.lbl_fin)
        form.addRow("Vigente desde:", self.date_desde)
        layout.addWidget(tarjeta)
        layout.addWidget(theme.boton("Agregar horario", "confirmar", self._agregar))

        self.time_inicio.timeChanged.connect(self._actualizar_fin)
        self.spin_clases.valueChanged.connect(self._actualizar_fin)
        self._actualizar_fin()

    def _hora_fin(self):
        inicio = datetime.combine(date.today(), self.time_inicio.time().toPython())
        return inicio + timedelta(minutes=MINUTOS_MODULO * self.spin_clases.value())

    def _actualizar_fin(self):
        self.lbl_fin.setText(self._hora_fin().strftime("%H:%M"))

    def refrescar(self):
        try:
            docentes = docente_repository.listar_docentes(solo_activos=True)
            catedras = repo.listar_catedras()
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.recargar_combo(
            self.combo_docente, [(theme.nombre_docente(d), d["id"]) for d in docentes]
        )
        theme.recargar_combo(
            self.combo_catedra,
            [(f"{c['nombre']} - {c['carrera']}", c["id"]) for c in catedras],
        )
        self._cargar_horarios()

    def _cargar_horarios(self):
        docente_id = self.combo_docente.currentData()
        if docente_id is None:
            self.tabla.setRowCount(0)
            return
        try:
            horarios = repo.listar_horarios(docente_id)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    theme.DIAS_SEMANA[h["dia_semana"]],
                    f"{theme.hora(h['hora_inicio'])} - {theme.hora(h['hora_fin'])}",
                    h["catedra"],
                    h["carrera"],
                    theme.fecha(h["vigente_desde"]),
                    theme.fecha(h["vigente_hasta"]) or "Sin fecha de baja",
                ]
                for h in horarios
            ],
            [h["id"] for h in horarios],
        )

    def _agregar(self):
        docente_id = self.combo_docente.currentData()
        catedra_id = self.combo_catedra.currentData()
        if docente_id is None or catedra_id is None:
            theme.avisar(
                self, "Datos faltantes", "Se necesita al menos un docente y una cátedra."
            )
            return
        inicio = self.time_inicio.time().toPython()
        fin = self._hora_fin()
        if fin.date() != date.today():
            theme.avisar(self, "Horario inválido", "El bloque no puede pasar de la medianoche.")
            return
        dia = self.combo_dia.currentData()
        desde = self.date_desde.date().toPython()
        try:
            pisados = repo.horarios_superpuestos(docente_id, dia, inicio, fin.time(), desde)
            if pisados:
                p = pisados[0]
                theme.avisar(
                    self, "Horario superpuesto",
                    f"El docente ya tiene {p['catedra']} ese día de "
                    f"{theme.hora(p['hora_inicio'])} a {theme.hora(p['hora_fin'])}.",
                )
                return
            repo.crear_horario(docente_id, catedra_id, dia, inicio, fin.time(), desde)
        except Exception as e:
            theme.error_bd(self, e)
            return
        self._cargar_horarios()

    def _seleccionado(self):
        horario_id = theme.id_seleccionado(self.tabla)
        if horario_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná un horario de la lista.")
        return horario_id

    def _finalizar(self):
        horario_id = self._seleccionado()
        if horario_id is None:
            return
        try:
            repo.finalizar_horario(horario_id, date.today())
        except Exception as e:
            theme.avisar(
                self, "No se pudo dar de baja",
                "El horario todavía no está vigente: usá Eliminar." if "check" in str(e).lower()
                else str(e),
            )
        self._cargar_horarios()

    def _eliminar(self):
        horario_id = self._seleccionado()
        if horario_id is None:
            return
        try:
            repo.eliminar_horario(horario_id)
        except Exception as e:
            if "foreign key" in str(e).lower():
                theme.avisar(
                    self, "No se puede eliminar",
                    "El horario ya tiene marcaciones. Usá 'Dar de baja desde hoy' "
                    "para conservar el historial.",
                )
            else:
                theme.error_bd(self, e)
        self._cargar_horarios()

    def _descargar_planilla(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar planilla modelo", "planilla_horarios.xlsx", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        try:
            importacion_service.generar_planilla(ruta)
        except Exception as e:
            theme.avisar(self, "No se pudo guardar", f"No se pudo generar la planilla:\n{e}")
            return
        theme.informar(self, "Planilla generada", f"La planilla se guardó en:\n{ruta}")

    def _importar(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir planilla de horarios", "", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        try:
            bloques, errores = importacion_service.leer_planilla(ruta)
        except Exception as e:
            theme.avisar(self, "No se pudo leer", f"No se pudo abrir la planilla:\n{e}")
            return
        if not bloques:
            theme.avisar(
                self, "Nada para importar",
                "\n".join(errores) or "La planilla no tiene horarios cargados.",
            )
            return
        ImportarHorariosDialog(bloques, errores, self).exec()
        self.refrescar()
