from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from repositories import docente_repository
from services import importacion_docentes_service
from ui import theme
from ui.importar_horarios_dialog import COLOR_ERROR, COLOR_OMITIDO


class ImportarDocentesDialog(QDialog):
    """Vista previa del listado: muestra qué se va a crear y recién guarda al confirmar."""

    def __init__(self, docentes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importar docentes")
        self.resize(1180, 600)

        layout = QVBoxLayout(self)
        layout.addWidget(theme.etiqueta("Vista previa de la importación"))
        self.lbl_resumen = QLabel()
        self.lbl_resumen.setWordWrap(True)
        layout.addWidget(self.lbl_resumen)
        self.tabla = theme.crear_tabla(
            ["Fila", "Docente", "DNI", "CUIL", "Celular", "Correo", "Resultado"]
        )
        layout.addWidget(self.tabla, 1)
        fila = QHBoxLayout()
        fila.addStretch()
        self.btn_importar = theme.boton("Importar", "confirmar", self._importar)
        fila.addWidget(self.btn_importar)
        fila.addWidget(theme.boton("Cancelar", "neutro", self.reject))
        layout.addLayout(fila)

        self.plan = importacion_docentes_service.planificar(
            docentes, docente_repository.listar_docentes()
        )
        self._mostrar()

    def _mostrar(self):
        plan = self.plan
        filas = (
            [
                (d, f"Se crea ({d['aviso']})" if d["aviso"] else "Se crea",
                 COLOR_ERROR if d["aviso"] else None)
                for d in plan["nuevos"]
            ]
            + [
                (d, "Ya existe: se completa "
                    + importacion_docentes_service.descripcion_faltantes(faltantes), None)
                for d, _, faltantes in plan["completados"]
            ]
            + [(d, "Ya estaba cargado", COLOR_OMITIDO) for d in plan["sin_cambios"]]
            + [(d, f"No se importa: {motivo}", COLOR_ERROR) for d, motivo in plan["errores"]]
        )
        filas.sort(key=lambda f: f[0]["fila"])
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    d["fila"], f"{d['apellido']}, {d['nombre']}", d["dni"], d["cuil"],
                    d["celular"], d["correo_electronico"], resultado,
                ]
                for d, resultado, _ in filas
            ],
        )
        for i, (_, _, color) in enumerate(filas):
            if color:
                for j in range(self.tabla.columnCount()):
                    self.tabla.item(i, j).setForeground(color)
        self.lbl_resumen.setText(
            f"Docentes a crear: {len(plan['nuevos'])}. "
            f"Ya existentes a los que se les completan datos: {len(plan['completados'])}. "
            f"Ya estaban cargados: {len(plan['sin_cambios'])}. "
            f"Con errores: {len(plan['errores'])}.\n"
            "Los docentes nuevos quedan sin fotos: hay que tomárselas en Docentes "
            "para que puedan marcar."
        )
        self.btn_importar.setEnabled(bool(plan["nuevos"] or plan["completados"]))

    def _importar(self):
        try:
            docente_repository.importar_docentes(self.plan["nuevos"], self.plan["completados"])
        except Exception as e:
            theme.avisar(
                self, "No se pudo importar", f"No se guardó ningún dato del listado:\n{e}"
            )
            return
        theme.informar(
            self, "Importación terminada",
            f"Docentes creados: {len(self.plan['nuevos'])}. "
            f"Docentes completados: {len(self.plan['completados'])}.",
        )
        self.accept()
