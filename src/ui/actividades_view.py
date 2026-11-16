from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from repositories import academico_repository, docente_repository
from repositories import actividad_repository as repo
from repositories.asistencia_repository import ROLES, TIPOS_ACTIVIDAD
from services import report_service
from ui import theme

MESA = "mesa_examen"
JORNADA = "jornada_institucional"


class ActividadesView(QWidget):
    """Jornadas institucionales y mesas de examen, con sus participantes."""

    def __init__(self, nombre_usuario=""):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Actividades
        izquierda = QVBoxLayout()
        izquierda.addWidget(theme.etiqueta("Actividades especiales"))
        izquierda.addWidget(
            theme.etiqueta(
                "Jornadas institucionales y mesas de examen. Se marcan con las mismas "
                "reglas de entrada y salida que una clase.",
                "subtitulo",
            )
        )
        self.tabla = theme.crear_tabla(["Fecha", "Horario", "Tipo", "Descripción", "Docentes"])
        encabezado = self.tabla.horizontalHeader()
        for columna in (0, 1, 2, 4):
            encabezado.setSectionResizeMode(columna, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.itemSelectionChanged.connect(self._cargar_participantes)
        izquierda.addWidget(self.tabla)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        form = QFormLayout(tarjeta)
        self.combo_tipo = theme.combo([(TIPOS_ACTIVIDAD[t], t) for t in (MESA, JORNADA)])
        self.combo_tipo.currentIndexChanged.connect(self._tipo_cambiado)
        self.input_descripcion = QLineEdit()
        self.combo_catedra = theme.combo([])
        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setCalendarPopup(True)
        self.time_inicio = QTimeEdit(QTime(8, 0))
        self.time_fin = QTimeEdit(QTime(12, 0))
        for campo in (self.time_inicio, self.time_fin):
            campo.setDisplayFormat("HH:mm")
        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Descripción:", self.input_descripcion)
        form.addRow("Cátedra (mesas):", self.combo_catedra)
        form.addRow("Fecha:", self.date_fecha)
        form.addRow("Hora de inicio:", self.time_inicio)
        form.addRow("Hora de fin:", self.time_fin)
        izquierda.addWidget(tarjeta)
        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Agregar actividad", "confirmar", self._agregar))
        fila.addWidget(theme.boton("Eliminar", "peligro", self._eliminar))
        izquierda.addLayout(fila)
        fila = QHBoxLayout()
        fila.addWidget(
            theme.boton("Exportar a Excel", "secundario", lambda: self._exportar("xlsx"))
        )
        fila.addWidget(
            theme.boton("Exportar a PDF", "secundario", lambda: self._exportar("pdf"))
        )
        izquierda.addLayout(fila)
        layout.addLayout(izquierda, 6)

        # Participantes
        derecha = QVBoxLayout()
        self.lbl_participantes = theme.etiqueta("Docentes de la actividad", "seccion")
        derecha.addWidget(self.lbl_participantes)
        self.tabla_participantes = theme.crear_tabla(["Docente", "Rol"])
        derecha.addWidget(self.tabla_participantes)
        self.combo_docente = theme.combo([])
        self.combo_rol = theme.combo([(nombre, rol) for rol, nombre in ROLES.items()])
        derecha.addWidget(self.combo_docente)
        derecha.addWidget(self.combo_rol)
        derecha.addWidget(theme.boton("Agregar docente", "confirmar", self._agregar_docente))
        derecha.addWidget(
            theme.boton("Agregar a todos los docentes", "secundario", self._agregar_todos)
        )
        derecha.addWidget(theme.boton("Quitar docente", "peligro", self._quitar_docente))
        layout.addLayout(derecha, 4)

        self.actividades = {}

    def _tipo_cambiado(self):
        self.combo_catedra.setEnabled(self.combo_tipo.currentData() == MESA)

    def refrescar(self, mantener_seleccion=False):
        """Al entrar a la pantalla o terminar una acción, la lista queda sin selección."""
        try:
            actividades = repo.listar_actividades()
            docentes = docente_repository.listar_docentes(solo_activos=True)
            catedras = academico_repository.listar_catedras()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.actividades = {a["id"]: a for a in actividades}
        seleccion = theme.id_seleccionado(self.tabla) if mantener_seleccion else None
        self.tabla.blockSignals(True)
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    theme.fecha(a["fecha"]),
                    f"{theme.hora(a['hora_inicio'])} - {theme.hora(a['hora_fin'])}",
                    TIPOS_ACTIVIDAD[a["tipo"]],
                    a["descripcion"] + (f" ({a['catedra']})" if a["catedra"] else ""),
                    a["participantes"],
                ]
                for a in actividades
            ],
            [a["id"] for a in actividades],
        )
        ids = [a["id"] for a in actividades]
        if seleccion in ids:
            self.tabla.selectRow(ids.index(seleccion))
        self.tabla.blockSignals(False)
        theme.recargar_combo(
            self.combo_docente, [(theme.nombre_docente(d), d["id"]) for d in docentes]
        )
        theme.recargar_combo(
            self.combo_catedra,
            [(f"{c['nombre']} - {c['carrera']}", c["id"]) for c in catedras],
        )
        self._tipo_cambiado()
        self._cargar_participantes()

    def _cargar_participantes(self):
        actividad_id = theme.id_seleccionado(self.tabla)
        if actividad_id is None:
            self.tabla_participantes.setRowCount(0)
            self.lbl_participantes.setText("Docentes de la actividad")
            return
        actividad = self.actividades[actividad_id]
        self.lbl_participantes.setText(f"Docentes de: {actividad['descripcion']}")
        # El rol sólo existe en las mesas de examen
        self.combo_rol.setEnabled(actividad["tipo"] == MESA)
        try:
            participantes = repo.listar_participantes(actividad_id)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.llenar_tabla(
            self.tabla_participantes,
            [
                [theme.nombre_docente(p), ROLES.get(p["rol"], "Participante")]
                for p in participantes
            ],
            [p["id"] for p in participantes],
        )

    def _agregar(self):
        tipo = self.combo_tipo.currentData()
        descripcion = self.input_descripcion.text().strip()
        inicio = self.time_inicio.time().toPython()
        fin = self.time_fin.time().toPython()
        if not descripcion:
            theme.avisar(self, "Dato faltante", "Ingresá una descripción de la actividad.")
            return
        if fin <= inicio:
            theme.avisar(
                self, "Horario inválido", "La hora de fin debe ser posterior a la de inicio."
            )
            return
        catedra_id = self.combo_catedra.currentData() if tipo == MESA else None
        if tipo == MESA and catedra_id is None:
            theme.avisar(self, "Dato faltante", "Una mesa de examen necesita una cátedra.")
            return
        try:
            repo.crear_actividad(
                tipo, descripcion, self.date_fecha.date().toPython(), inicio, fin, catedra_id
            )
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.input_descripcion.clear()
        self.refrescar()

    def _actividad_seleccionada(self):
        actividad_id = theme.id_seleccionado(self.tabla)
        if actividad_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná una actividad de la lista.")
        return actividad_id

    def _eliminar(self):
        actividad_id = self._actividad_seleccionada()
        if actividad_id is None:
            return
        try:
            repo.eliminar_actividad(actividad_id)
        except Exception as e:
            if "foreign key" in str(e).lower():
                theme.avisar(
                    self, "No se puede eliminar",
                    "La actividad ya tiene marcaciones de docentes.",
                )
            else:
                theme.error_bd(self, e)
        self.refrescar()

    def _agregar_docente(self):
        actividad_id = self._actividad_seleccionada()
        docente_id = self.combo_docente.currentData()
        if actividad_id is None or docente_id is None:
            return
        es_mesa = self.actividades[actividad_id]["tipo"] == MESA
        try:
            repo.agregar_participante(
                actividad_id, docente_id, self.combo_rol.currentData() if es_mesa else None
            )
        except Exception as e:
            if "unique" in str(e).lower():
                theme.avisar(self, "Docente repetido", "Ese docente ya está en la actividad.")
            else:
                theme.error_bd(self, e)
        self.refrescar(mantener_seleccion=True)

    def _agregar_todos(self):
        actividad_id = self._actividad_seleccionada()
        if actividad_id is None:
            return
        if self.actividades[actividad_id]["tipo"] == MESA:
            theme.avisar(
                self, "Sólo para jornadas",
                "En una mesa de examen los docentes se agregan de a uno, con su rol.",
            )
            return
        try:
            repo.agregar_todos_los_docentes(actividad_id)
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar(mantener_seleccion=True)

    def _quitar_docente(self):
        participacion_id = theme.id_seleccionado(self.tabla_participantes)
        if participacion_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná un docente de la actividad.")
            return
        try:
            repo.quitar_participante(participacion_id)
        except Exception as e:
            if "foreign key" in str(e).lower():
                theme.avisar(
                    self, "No se puede quitar", "Ese docente ya marcó asistencia en la actividad."
                )
            else:
                theme.error_bd(self, e)
        self.refrescar(mantener_seleccion=True)

    def _exportar(self, extension):
        if not self.actividades:
            theme.avisar(self, "Sin actividades", "No hay actividades para exportar.")
            return
        filtro = "Excel (*.xlsx)" if extension == "xlsx" else "PDF (*.pdf)"
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar listado de actividades",
            f"actividades_especiales.{extension}", filtro,
        )
        if not ruta:
            return
        if not ruta.lower().endswith("." + extension):
            ruta += "." + extension
        try:
            filas = report_service.filas_actividades(
                [
                    (a, repo.listar_participantes(a["id"]))
                    for a in self.actividades.values()
                ],
                TIPOS_ACTIVIDAD, ROLES,
            )
            if extension == "xlsx":
                report_service.generar_excel_actividades(ruta, filas, self.nombre_usuario)
            else:
                report_service.generar_pdf_actividades(
                    ruta, filas, self.nombre_usuario, theme.RUTA_ESCUDO
                )
        except Exception as e:
            theme.avisar(self, "No se pudo exportar", f"No se pudo generar el archivo:\n{e}")
            return
        theme.informar(self, "Listado generado", f"El listado se guardó en:\n{ruta}")
