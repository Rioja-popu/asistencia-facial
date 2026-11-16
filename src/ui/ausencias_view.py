from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from repositories import ausencia_repository as repo
from repositories import docente_repository
from ui import theme

TIPOS = {"particular": "Particular", "medica": "Médica"}
ESTADOS = {
    "registrada": "Registrada",
    "pendiente_certificado": "Certificado pendiente",
    "justificada": "Justificada",
    "no_justificada": "No justificada",
}


class AusenciasView(QWidget):
    """Particulares y ausencias médicas, con el seguimiento de los certificados."""

    def __init__(self, usuario_id):
        super().__init__()
        self.usuario_id = usuario_id
        self.ausencias = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Ausencias y justificaciones"))
        layout.addWidget(
            theme.etiqueta(
                f"Cada docente dispone de {repo.PARTICULARES_POR_ANIO} particulares por año. "
                "Una ausencia médica queda pendiente hasta que se presenta el certificado.",
                "subtitulo",
            )
        )

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        form = QFormLayout(tarjeta)
        self.combo_docente = theme.combo([])
        self.combo_docente.currentIndexChanged.connect(self._actualizar_contador)
        self.combo_tipo = theme.combo([(nombre, tipo) for tipo, nombre in TIPOS.items()])
        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha.setCalendarPopup(True)
        self.date_fecha.dateChanged.connect(self._actualizar_contador)
        self.input_observacion = QLineEdit()
        self.lbl_contador = theme.etiqueta("", "subtitulo")
        form.addRow("Docente:", self.combo_docente)
        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Fecha de la ausencia:", self.date_fecha)
        form.addRow("Observación:", self.input_observacion)
        form.addRow("Particulares:", self.lbl_contador)
        layout.addWidget(tarjeta)
        layout.addWidget(theme.boton("Registrar ausencia", "confirmar", self._registrar))

        self.chk_pendientes = QCheckBox("Mostrar sólo certificados pendientes")
        self.chk_pendientes.toggled.connect(self._cargar_tabla)
        layout.addWidget(self.chk_pendientes)
        self.tabla = theme.crear_tabla(
            ["Fecha", "Docente", "Tipo", "Estado", "Certificado", "Observación", "Cargó"],
            "No hay ausencias cargadas.",
        )
        layout.addWidget(self.tabla)

        fila = QHBoxLayout()
        fila.addWidget(
            theme.boton("Certificado presentado", "confirmar", lambda: self._resolver(True))
        )
        fila.addWidget(
            theme.boton("No presentó certificado", "secundario", lambda: self._resolver(False))
        )
        fila.addWidget(theme.boton("Eliminar (cargada por error)", "peligro", self._eliminar))
        fila.addStretch()
        layout.addLayout(fila)

    def refrescar(self):
        try:
            docentes = docente_repository.listar_docentes(solo_activos=True)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.recargar_combo(
            self.combo_docente, [(theme.nombre_docente(d), d["id"]) for d in docentes]
        )
        self._actualizar_contador()
        self._cargar_tabla()

    def _actualizar_contador(self):
        docente_id = self.combo_docente.currentData()
        if docente_id is None:
            self.lbl_contador.setText("")
            return
        anio = self.date_fecha.date().year()
        try:
            usados = repo.contar_particulares(docente_id, anio)
        except Exception as e:
            self.lbl_contador.setText(str(e))
            return
        self.lbl_contador.setText(
            f"{usados} de {repo.PARTICULARES_POR_ANIO} utilizados en {anio}"
        )

    def _cargar_tabla(self):
        try:
            ausencias = repo.listar_ausencias(solo_pendientes=self.chk_pendientes.isChecked())
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.ausencias = {a["id"]: a for a in ausencias}
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    theme.fecha(a["fecha"]),
                    theme.nombre_docente(a),
                    TIPOS[a["tipo"]],
                    ESTADOS[a["estado"]],
                    theme.fecha(a["certificado_presentado_el"]),
                    a["observacion"],
                    a["nombre_usuario"],
                ]
                for a in ausencias
            ],
            [a["id"] for a in ausencias],
        )

    def _registrar(self):
        docente_id = self.combo_docente.currentData()
        if docente_id is None:
            theme.avisar(self, "Dato faltante", "Primero registrá un docente.")
            return
        try:
            repo.registrar_ausencia(
                docente_id,
                self.date_fecha.date().toPython(),
                self.combo_tipo.currentData(),
                self.input_observacion.text().strip(),
                self.usuario_id,
            )
        except ValueError as e:
            theme.avisar(self, "No se puede registrar", str(e))
            return
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.input_observacion.clear()
        self.refrescar()

    def _seleccionada(self):
        ausencia_id = theme.id_seleccionado(self.tabla)
        if ausencia_id is None:
            theme.avisar(self, "Sin selección", "Seleccioná una ausencia de la lista.")
            return None
        return self.ausencias[ausencia_id]

    def _resolver(self, justificada):
        ausencia = self._seleccionada()
        if ausencia is None:
            return
        if ausencia["tipo"] != "medica":
            theme.avisar(
                self, "No corresponde", "Los particulares no requieren certificado."
            )
            return
        try:
            repo.resolver_medica(ausencia["id"], justificada, date.today())
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar()

    def _eliminar(self):
        ausencia = self._seleccionada()
        if ausencia is None:
            return
        if not theme.confirmar(
            self, "Eliminar ausencia",
            f"¿Eliminar la ausencia de {theme.nombre_docente(ausencia)} "
            f"del {theme.fecha(ausencia['fecha'])}?",
        ):
            return
        try:
            repo.eliminar_ausencia(ausencia["id"])
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar()
