from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QSpinBox, QVBoxLayout, QWidget

from repositories import academico_repository as repo
from ui import theme


class CatedrasView(QWidget):
    """Carreras del instituto y cátedras de cada carrera."""

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Carreras
        carreras = QVBoxLayout()
        carreras.addWidget(theme.etiqueta("Carreras"))
        self.tabla_carreras = theme.crear_tabla(["Carrera"])
        carreras.addWidget(self.tabla_carreras)
        self.input_carrera = QLineEdit()
        self.input_carrera.setPlaceholderText("Nombre de la carrera")
        carreras.addWidget(self.input_carrera)
        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Agregar carrera", "confirmar", self._agregar_carrera))
        fila.addWidget(theme.boton("Eliminar", "peligro", self._eliminar_carrera))
        carreras.addLayout(fila)
        layout.addLayout(carreras, 4)

        # Cátedras
        catedras = QVBoxLayout()
        catedras.addWidget(theme.etiqueta("Cátedras"))
        self.tabla_catedras = theme.crear_tabla(["Cátedra", "Año", "Carrera"])
        catedras.addWidget(self.tabla_catedras)
        fila = QHBoxLayout()
        self.combo_carrera = theme.combo([])
        self.input_catedra = QLineEdit()
        self.input_catedra.setPlaceholderText("Nombre de la cátedra")
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(1, 6)
        self.spin_anio.setPrefix("Año ")
        fila.addWidget(self.combo_carrera, 3)
        fila.addWidget(self.input_catedra, 3)
        fila.addWidget(self.spin_anio, 1)
        catedras.addLayout(fila)
        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Agregar cátedra", "confirmar", self._agregar_catedra))
        fila.addWidget(theme.boton("Eliminar", "peligro", self._eliminar_catedra))
        catedras.addLayout(fila)
        layout.addLayout(catedras, 7)

    def refrescar(self):
        try:
            carreras = repo.listar_carreras()
            catedras = repo.listar_catedras()
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.llenar_tabla(
            self.tabla_carreras, [[c["nombre"]] for c in carreras], [c["id"] for c in carreras]
        )
        theme.llenar_tabla(
            self.tabla_catedras,
            [[c["nombre"], f"{c['anio']}º", c["carrera"]] for c in catedras],
            [c["id"] for c in catedras],
        )
        theme.recargar_combo(self.combo_carrera, [(c["nombre"], c["id"]) for c in carreras])

    def _ejecutar(self, accion, mensaje_en_uso):
        try:
            accion()
        except Exception as e:
            texto = str(e).lower()
            if "foreign key" in texto or "unique" in texto:
                theme.avisar(self, "No se pudo completar", mensaje_en_uso)
            else:
                theme.error_bd(self, e)
        self.refrescar()

    def _agregar_carrera(self):
        nombre = self.input_carrera.text().strip()
        if not nombre:
            theme.avisar(self, "Dato faltante", "Ingresá el nombre de la carrera.")
            return
        self._ejecutar(lambda: repo.crear_carrera(nombre), "Ya existe una carrera con ese nombre.")
        self.input_carrera.clear()

    def _eliminar_carrera(self):
        carrera_id = theme.id_seleccionado(self.tabla_carreras)
        if carrera_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná una carrera de la lista.")
            return
        self._ejecutar(
            lambda: repo.eliminar_carrera(carrera_id),
            "La carrera tiene cátedras cargadas y no se puede eliminar.",
        )

    def _agregar_catedra(self):
        nombre = self.input_catedra.text().strip()
        carrera_id = self.combo_carrera.currentData()
        if carrera_id is None:
            theme.avisar(self, "Dato faltante", "Primero cargá una carrera.")
            return
        if not nombre:
            theme.avisar(self, "Dato faltante", "Ingresá el nombre de la cátedra.")
            return
        self._ejecutar(
            lambda: repo.crear_catedra(carrera_id, nombre, self.spin_anio.value()),
            "Esa carrera ya tiene una cátedra con ese nombre.",
        )
        self.input_catedra.clear()

    def _eliminar_catedra(self):
        catedra_id = theme.id_seleccionado(self.tabla_catedras)
        if catedra_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná una cátedra de la lista.")
            return
        self._ejecutar(
            lambda: repo.eliminar_catedra(catedra_id),
            "La cátedra tiene horarios o mesas de examen asociados y no se puede eliminar.",
        )
