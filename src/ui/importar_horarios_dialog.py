from PySide6.QtCore import QDate
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDateEdit, QDialog, QHBoxLayout, QLabel, QVBoxLayout

from repositories import academico_repository, docente_repository, importacion_repository
from services import importacion_service
from ui import theme

COLOR_ERROR = QColor("#c0392b")
COLOR_OMITIDO = QColor("#7a8794")


class ImportarHorariosDialog(QDialog):
    """Vista previa de la planilla: muestra qué se va a crear y recién guarda al confirmar."""

    def __init__(self, bloques, errores_lectura, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar horarios")
        self.resize(980, 620)
        self.bloques = bloques
        self.errores_lectura = errores_lectura
        self.plan = None

        layout = QVBoxLayout(self)
        layout.addWidget(theme.etiqueta("Vista previa de la importación"))
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setWordWrap(True)
        layout.addWidget(self.lbl_resumen)

        self.tabla = theme.crear_tabla(
            ["Curso", "Día", "Horario", "Cátedra", "Docente", "Resultado"]
        )
        layout.addWidget(self.tabla, 1)

        self.lbl_errores = QLabel()
        self.lbl_errores.setWordWrap(True)
        self.lbl_errores.setStyleSheet(f"color: {COLOR_ERROR.name()};")
        layout.addWidget(self.lbl_errores)

        fila = QHBoxLayout()
        fila.addWidget(QLabel("Horarios vigentes desde:"))
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setCalendarPopup(True)
        self.date_desde.dateChanged.connect(self._planificar)
        fila.addWidget(self.date_desde)
        fila.addStretch()
        self.btn_importar = theme.boton("Importar", "confirmar", self._importar)
        fila.addWidget(self.btn_importar)
        fila.addWidget(theme.boton("Cancelar", "neutro", self.reject))
        layout.addLayout(fila)

        self._planificar()

    def _planificar(self):
        self.btn_importar.setEnabled(False)
        try:
            self.plan = importacion_service.planificar(
                self.bloques,
                academico_repository.listar_carreras(),
                academico_repository.listar_catedras(),
                docente_repository.listar_docentes(),
                importacion_repository.listar_horarios_vigentes(
                    self.date_desde.date().toPython()
                ),
            )
        except Exception as e:
            theme.error_bd(self, e)
            return
        plan = self.plan
        filas = (
            [(h, "Se crea", None) for h in plan["horarios"]]
            + [(h, "Ya estaba cargado", COLOR_OMITIDO) for h in plan["omitidos"]]
            + [(h, f"No se importa: {motivo}", COLOR_ERROR) for h, motivo in plan["errores"]]
        )
        filas.sort(key=lambda f: (f[0]["carrera"], f[0]["anio"], f[0]["dia"], f[0]["inicio"]))
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    f"{h['anio']}° - {h['carrera']}",
                    importacion_service.NOMBRES_DIAS[h["dia"]],
                    f"{theme.hora(h['inicio'])} - {theme.hora(h['fin'])}",
                    h["catedra"],
                    f"{h['apellido']}, {h['nombre']}",
                    resultado,
                ]
                for h, resultado, _ in filas
            ],
        )
        for i, (_, _, color) in enumerate(filas):
            if color:
                for j in range(self.tabla.columnCount()):
                    self.tabla.item(i, j).setForeground(color)

        self.lbl_resumen.setText(
            f"Horarios a crear: {len(plan['horarios'])}. "
            f"Carreras nuevas: {len(plan['carreras_nuevas'])}. "
            f"Cátedras nuevas: {len(plan['catedras_nuevas'])}. "
            f"Docentes nuevos: {len(plan['docentes_nuevos'])}. "
            f"Ya estaban cargados: {len(plan['omitidos'])}. "
            f"Con errores: {len(plan['errores']) + len(self.errores_lectura)}.\n"
            "Los docentes nuevos quedan sin DNI, CUIL ni fotos: hay que completarlos "
            "en Docentes para que puedan marcar."
        )
        self.lbl_errores.setText("\n".join(self.errores_lectura[:8]))
        self.lbl_errores.setVisible(bool(self.errores_lectura))
        self.btn_importar.setEnabled(bool(plan["horarios"]))

    def _importar(self):
        try:
            importacion_repository.importar(
                self.plan["horarios"], self.date_desde.date().toPython()
            )
        except Exception as e:
            theme.avisar(
                self, "No se pudo importar",
                f"No se guardó ningún dato de la planilla:\n{e}",
            )
            return
        theme.informar(
            self, "Importación terminada",
            f"Horarios creados: {len(self.plan['horarios'])}.",
        )
        self.accept()
