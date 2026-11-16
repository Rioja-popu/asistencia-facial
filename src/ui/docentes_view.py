from PySide6.QtCore import QRegularExpression, Qt
from PySide6.QtGui import QImage, QPixmap, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from repositories import docente_repository
from services import importacion_docentes_service
from ui import theme
from ui.camera_dialog import CameraCaptureDialog
from ui.importar_docentes_dialog import ImportarDocentesDialog

ANGULOS = [
    ("Ángulo frontal", "frontal"),
    ("Ángulo izquierdo", "lateral_izquierdo"),
    ("Ángulo derecho", "lateral_derecho"),
]


class PhotoSectionWidget(QWidget):
    """Componente para gestionar la carga, previsualización y borrado de cada ángulo facial."""

    def __init__(self, titulo, angulo_key):
        super().__init__()
        self.angulo_key = angulo_key
        self.image_bytes = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 15)

        # Título de la sección
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            "font-weight: bold; font-size: 13px;"
        )
        layout.addWidget(lbl_titulo)

        # Botones de acción
        btn_layout = QHBoxLayout()
        self.btn_cargar = QPushButton("Cargar Foto")
        self.btn_tomar = QPushButton("Tomar Foto")
        # En el __init__ de PhotoSectionWidget, después de crear self.btn_tomar:
        self.btn_tomar.clicked.connect(self._tomar_foto)

        for btn in (self.btn_cargar, self.btn_tomar):
            btn.setProperty("rol", "secundario")
            btn_layout.addWidget(btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        # Panel de visualización + Botón de Papelera
        preview_layout = QHBoxLayout()

        self.lbl_preview = QLabel("Sin imagen todavía")
        self.lbl_preview.setFixedSize(200, 150)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet(
            """
            QLabel {
                border: 2px dashed #bdc3c7;
                border-radius: 6px;
                background-color: #f8f9fa;
                color: #7f8c8d;
            }
        """
        )
        preview_layout.addWidget(self.lbl_preview)

        # Botón Papelera (inicialmente oculto)
        self.btn_borrar = QPushButton("🗑️")
        self.btn_borrar.setFixedSize(35, 35)
        self.btn_borrar.setToolTip("Eliminar foto")
        self.btn_borrar.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """
        )
        self.btn_borrar.hide()
        preview_layout.addWidget(self.btn_borrar)
        preview_layout.addStretch()

        layout.addLayout(preview_layout)

        # Eventos
        self.btn_cargar.clicked.connect(self._cargar_foto)
        self.btn_borrar.clicked.connect(self.limpiar)

    def _tomar_foto(self):
        dialog = CameraCaptureDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            image_bytes = dialog.captured_frame_bytes
            if image_bytes:
                self.image_bytes = image_bytes

                q_img = QImage.fromData(image_bytes)
                pixmap = QPixmap.fromImage(q_img)

                # Asegúrate de usar el nombre real de tu QLabel de vista previa
                self.lbl_preview.setPixmap(
                    pixmap.scaled(
                        self.lbl_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                # MOSTRAR EL BOTÓN DE BORRAR
                self.btn_borrar.show()

    def _cargar_foto(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Imagen",
            "",
            "Archivos de Imagen (*.png *.jpg *.jpeg *.bmp)",
        )
        if file_path:
            with open(file_path, "rb") as f:
                self.image_bytes = f.read()

            pixmap = QPixmap(file_path)
            self.lbl_preview.setPixmap(
                pixmap.scaled(
                    self.lbl_preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.btn_borrar.show()

    def mostrar(self, image_bytes):
        """Muestra una foto ya guardada, sin marcarla como foto nueva."""
        pixmap = QPixmap.fromImage(QImage.fromData(image_bytes))
        self.lbl_preview.setPixmap(
            pixmap.scaled(
                self.lbl_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def limpiar(self):
        self.image_bytes = None
        self.lbl_preview.clear()
        self.lbl_preview.setText("Sin imagen todavía")
        self.btn_borrar.hide()


class DocentesView(QWidget):
    """Alta y edición de docentes con sus tres fotos de referencia."""

    def __init__(self):
        super().__init__()
        self.docente_id = None  # None = alta; con valor = edición

        layout = QHBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # Listado
        izquierda = QVBoxLayout()
        izquierda.addWidget(theme.etiqueta("Docentes"))
        izquierda.addWidget(
            theme.etiqueta("Seleccioná un docente para editarlo.", "subtitulo")
        )
        self.tabla = theme.crear_tabla(["Docente", "CUIL", "Estado"])
        self.tabla.itemSelectionChanged.connect(self._cargar_seleccionado)
        izquierda.addWidget(self.tabla)
        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Nuevo docente", al_hacer_clic=self._nuevo))
        self.btn_eliminar = theme.boton("Eliminar docente", "peligro", self._eliminar)
        self.btn_eliminar.setEnabled(False)
        fila.addWidget(self.btn_eliminar)
        izquierda.addLayout(fila)
        fila = QHBoxLayout()
        fila.addWidget(
            theme.boton("Descargar listado modelo", "secundario", self._descargar_listado)
        )
        fila.addWidget(theme.boton("Importar docentes", "secundario", self._importar))
        izquierda.addLayout(fila)
        layout.addLayout(izquierda, 5)

        # Formulario
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        contenedor = QWidget()
        contenedor.setObjectName("formulario")
        scroll.setStyleSheet(
            "QScrollArea, QWidget#formulario { background-color: transparent; }"
        )
        derecha = QVBoxLayout(contenedor)
        self.lbl_formulario = theme.etiqueta("Nuevo docente", "seccion")
        derecha.addWidget(self.lbl_formulario)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        form = QFormLayout(tarjeta)
        self.input_apellido = QLineEdit()
        self.input_nombre = QLineEdit()
        self.input_dni = QLineEdit()
        self.input_cuil = QLineEdit()
        self.input_celular = QLineEdit()
        self.input_correo = QLineEdit()
        # DNI, CUIL y celular sólo aceptan dígitos: no se pueden tipear letras ni símbolos
        for campo, maximo in (
            (self.input_dni, 8), (self.input_cuil, 11), (self.input_celular, 15),
        ):
            campo.setValidator(
                QRegularExpressionValidator(QRegularExpression(f"[0-9]{{0,{maximo}}}"), campo)
            )
        self.input_dni.setPlaceholderText("Sólo números, 7 u 8 dígitos")
        self.input_cuil.setPlaceholderText("Sólo números, 11 dígitos (sin guiones)")
        self.input_celular.setPlaceholderText("Sólo números")
        self.chk_activo = QCheckBox("Activo (puede marcar asistencia)")
        self.chk_activo.setChecked(True)
        form.addRow("Apellido:", self.input_apellido)
        form.addRow("Nombre:", self.input_nombre)
        form.addRow("DNI:", self.input_dni)
        form.addRow("CUIL:", self.input_cuil)
        form.addRow("Celular:", self.input_celular)
        form.addRow("Correo electrónico:", self.input_correo)
        form.addRow("", self.chk_activo)
        derecha.addWidget(tarjeta)

        derecha.addWidget(theme.etiqueta("Fotos para el reconocimiento facial", "seccion"))
        self.secciones = [PhotoSectionWidget(titulo, clave) for titulo, clave in ANGULOS]
        # Frontal arriba; izquierdo y derecho lado a lado
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(20)
        for seccion, (fila, columna) in zip(self.secciones, ((0, 0), (1, 0), (1, 1))):
            grilla.addWidget(seccion, fila, columna)
        grilla.setColumnStretch(2, 1)
        derecha.addLayout(grilla)

        self.btn_guardar = theme.boton("Guardar docente", "confirmar", self._guardar)
        derecha.addWidget(self.btn_guardar)
        derecha.addStretch()
        scroll.setWidget(contenedor)
        layout.addWidget(scroll, 6)

    def refrescar(self):
        try:
            docentes = docente_repository.listar_docentes()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.docentes = {d["id"]: d for d in docentes}
        self.tabla.blockSignals(True)
        theme.llenar_tabla(
            self.tabla,
            [
                [theme.nombre_docente(d), d["cuil"] or "Sin cargar", "Activo" if d["activo"] else "Inactivo"]
                for d in docentes
            ],
            [d["id"] for d in docentes],
        )
        self.tabla.clearSelection()
        self.tabla.blockSignals(False)

    def _nuevo(self):
        self.docente_id = None
        self.btn_eliminar.setEnabled(False)
        self.tabla.clearSelection()
        self.lbl_formulario.setText("Nuevo docente")
        for campo in (
            self.input_apellido, self.input_nombre, self.input_dni,
            self.input_cuil, self.input_celular, self.input_correo,
        ):
            campo.clear()
        self.chk_activo.setChecked(True)
        for seccion in self.secciones:
            seccion.limpiar()

    def _cargar_seleccionado(self):
        docente_id = theme.id_seleccionado(self.tabla)
        if docente_id is None:
            # Se deseleccionó la fila: el formulario vuelve a "Nuevo docente"
            self._nuevo()
            return
        docente = self.docentes[docente_id]
        self.docente_id = docente_id
        self.btn_eliminar.setEnabled(True)
        self.lbl_formulario.setText(f"Editar docente: {theme.nombre_docente(docente)}")
        self.input_apellido.setText(docente["apellido"])
        self.input_nombre.setText(docente["nombre"])
        self.input_dni.setText(docente["dni"] or "")
        self.input_cuil.setText(docente["cuil"] or "")
        self.input_celular.setText(docente["celular"] or "")
        self.input_correo.setText(docente["correo_electronico"] or "")
        self.chk_activo.setChecked(docente["activo"])
        try:
            fotos = docente_repository.obtener_fotos(docente_id)
        except Exception as e:
            theme.error_bd(self, e)
            return
        for seccion in self.secciones:
            seccion.limpiar()
            if seccion.angulo_key in fotos:
                seccion.mostrar(fotos[seccion.angulo_key])

    def _guardar(self):
        apellido = self.input_apellido.text().strip()
        nombre = self.input_nombre.text().strip()
        dni = self.input_dni.text().strip()
        cuil = self.input_cuil.text().strip()
        if not all((apellido, nombre, dni, cuil)):
            theme.avisar(
                self, "Campos incompletos", "Apellido, nombre, DNI y CUIL son obligatorios."
            )
            return
        celular = self.input_celular.text().strip()
        if not (dni.isdigit() and len(dni) in (7, 8)):
            theme.avisar(self, "DNI inválido", "El DNI lleva 7 u 8 números, sin puntos.")
            return
        if not (cuil.isdigit() and len(cuil) == 11):
            theme.avisar(self, "CUIL inválido", "El CUIL lleva 11 números, sin guiones.")
            return
        if celular and not celular.isdigit():
            theme.avisar(self, "Celular inválido", "El celular sólo lleva números.")
            return

        # Sólo se envían las fotos nuevas; al editar, las demás se conservan
        fotos = {s.angulo_key: s.image_bytes for s in self.secciones if s.image_bytes}
        if self.docente_id is None and len(fotos) < len(self.secciones):
            theme.avisar(
                self, "Fotos faltantes",
                "Para registrar un docente se necesitan las tres fotos "
                "(frontal, izquierda y derecha).",
            )
            return

        datos = (
            apellido, nombre, dni, cuil,
            celular or None,
            self.input_correo.text().strip() or None,
            self.chk_activo.isChecked(),
        )
        try:
            docente_repository.guardar_docente(datos, fotos, self.docente_id)
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                theme.avisar(
                    self, "Docente duplicado", "Ya existe un docente con ese DNI o CUIL."
                )
            else:
                theme.error_bd(self, e)
            return
        theme.informar(self, "Docente guardado", "Los datos del docente fueron guardados.")
        self.refrescar()
        self._nuevo()

    def _descargar_listado(self):
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar listado modelo", "listado_docentes.xlsx", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta += ".xlsx"
        try:
            importacion_docentes_service.generar_planilla(ruta)
        except Exception as e:
            theme.avisar(self, "No se pudo guardar", f"No se pudo generar el listado:\n{e}")
            return
        theme.informar(self, "Listado generado", f"El listado se guardó en:\n{ruta}")

    def _importar(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Elegir listado de docentes", "", "Excel o CSV (*.xlsx *.csv)"
        )
        if not ruta:
            return
        try:
            docentes, errores = importacion_docentes_service.leer_listado(ruta)
        except Exception as e:
            theme.avisar(self, "No se pudo leer", f"No se pudo abrir el listado:\n{e}")
            return
        if not docentes:
            theme.avisar(
                self, "Nada para importar",
                "\n".join(errores) or "El listado no tiene docentes cargados.",
            )
            return
        try:
            dialogo = ImportarDocentesDialog(docentes, self)
        except Exception as e:
            theme.error_bd(self, e)
            return
        dialogo.exec()
        self.refrescar()

    def _eliminar(self):
        if self.docente_id is None:
            return
        docente = self.docentes[self.docente_id]
        try:
            asociados = docente_repository.contar_registros_asociados(self.docente_id)
        except Exception as e:
            theme.error_bd(self, e)
            return
        detalle = ", ".join(
            f"{cantidad} {nombre}"
            for nombre, cantidad in (
                ("horario(s)", asociados["horarios"]),
                ("participación(es) en actividades", asociados["actividades"]),
                ("marcación(es) de asistencia", asociados["asistencias"]),
                ("ausencia(s)", asociados["ausencias"]),
            )
            if cantidad
        )
        texto = (
            f"¿Eliminar definitivamente a {theme.nombre_docente(docente)}?\n\n"
            "Se borran sus datos y sus fotos"
            + (f", y también: {detalle}" if detalle else "")
            + ".\nEsta acción no se puede deshacer.\n\n"
            "Si sólo querés que deje de marcar asistencia pero conservar su historial "
            "para los informes, desmarcá la casilla \"Activo\" y guardá."
        )
        if not theme.confirmar(self, "Eliminar docente", texto):
            return
        try:
            docente_repository.eliminar_docente(self.docente_id)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.informar(self, "Docente eliminado", "El docente fue eliminado.")
        self.refrescar()
        self._nuevo()
