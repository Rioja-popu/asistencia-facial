from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QLineEdit, QVBoxLayout, QWidget

from repositories import user_repository as repo
from services import usuario_service
from ui import theme
from ui.contrasenia_dialog import ContraseniaDialog, campo_contrasenia


class UsuariosView(QWidget):
    """Usuarios que operan el sistema. Sólo la ve el administrador."""

    def __init__(self, usuario_actual_id):
        super().__init__()
        self.usuario_actual_id = usuario_actual_id
        self.usuarios = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addWidget(theme.etiqueta("Usuarios"))
        layout.addWidget(
            theme.etiqueta(
                "El administrador crea y elimina usuarios. Los administrativos usan el "
                "resto del sistema. Se puede ingresar con el nombre de usuario, el correo, "
                "el DNI o el CUIL.",
                "subtitulo",
            )
        )

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        columnas = QHBoxLayout(tarjeta)
        izquierda, derecha = QFormLayout(), QFormLayout()
        self.input_nombre = QLineEdit()
        self.input_nombre.setMaxLength(50)
        self.combo_rol = theme.combo(
            [
                (usuario_service.ROLES[rol], rol)
                for rol in (usuario_service.ADMINISTRATIVO, usuario_service.ADMINISTRADOR)
            ]
        )
        self.input_contrasenia = campo_contrasenia()
        self.input_repetida = campo_contrasenia()
        self.input_correo = QLineEdit()
        self.input_dni = QLineEdit()
        self.input_cuil = QLineEdit()
        for campo in (self.input_correo, self.input_dni, self.input_cuil):
            campo.setMaxLength(255)
            campo.setPlaceholderText("Opcional")
        izquierda.addRow("Nombre de usuario:", self.input_nombre)
        izquierda.addRow("Rol:", self.combo_rol)
        izquierda.addRow("Contraseña:", self.input_contrasenia)
        izquierda.addRow("Repetir contraseña:", self.input_repetida)
        derecha.addRow("Correo electrónico:", self.input_correo)
        derecha.addRow("DNI:", self.input_dni)
        derecha.addRow("CUIL:", self.input_cuil)
        columnas.addLayout(izquierda, 1)
        columnas.addSpacing(20)
        columnas.addLayout(derecha, 1)
        layout.addWidget(tarjeta)
        layout.addWidget(theme.boton("Agregar usuario", "confirmar", self._agregar))

        self.tabla = theme.crear_tabla(
            ["Usuario", "Rol", "Correo electrónico", "DNI", "CUIL", "Estado"]
        )
        layout.addWidget(self.tabla)

        fila = QHBoxLayout()
        fila.addWidget(theme.boton("Restablecer contraseña", "secundario", self._restablecer))
        fila.addWidget(theme.boton("Reactivar", "secundario", self._reactivar))
        fila.addWidget(theme.boton("Eliminar", "peligro", self._eliminar))
        fila.addStretch()
        layout.addLayout(fila)

    def refrescar(self):
        try:
            usuarios = repo.listar()
        except Exception as e:
            theme.error_bd(self, e)
            return
        self.usuarios = {u["id"]: u for u in usuarios}
        theme.llenar_tabla(
            self.tabla,
            [
                [
                    u["nombre_usuario"]
                    + (" (vos)" if u["id"] == self.usuario_actual_id else ""),
                    usuario_service.ROLES[u["rol"]],
                    u["correo_electronico"],
                    u["dni"],
                    u["cuil"],
                    "Activo" if u["activo"] else "Inactivo",
                ]
                for u in usuarios
            ],
            [u["id"] for u in usuarios],
            {(i, 5): "bien" if u["activo"] else "neutro" for i, u in enumerate(usuarios)},
        )

    def _seleccionado(self):
        usuario = self.usuarios.get(theme.id_seleccionado(self.tabla))
        if usuario is None:
            theme.avisar(self, "Sin selección", "Seleccioná un usuario de la lista.")
        return usuario

    def _agregar(self):
        try:
            datos = usuario_service.preparar_alta(
                self.input_nombre.text(), self.combo_rol.currentData(),
                self.input_contrasenia.text(), self.input_repetida.text(),
                self.input_correo.text(), self.input_dni.text(), self.input_cuil.text(),
            )
            usuario_service.validar_sin_repetidos(datos, repo.listar())
        except ValueError as e:
            theme.avisar(self, "Datos inválidos", str(e))
            return
        except Exception as e:
            theme.error_bd(self, e)
            return
        try:
            repo.crear(datos)
        except Exception as e:
            theme.error_bd(self, e)
            return
        for campo in (
            self.input_nombre, self.input_contrasenia, self.input_repetida,
            self.input_correo, self.input_dni, self.input_cuil,
        ):
            campo.clear()
        self.combo_rol.setCurrentIndex(0)
        self.refrescar()

    def _restablecer(self):
        usuario = self._seleccionado()
        if usuario is None:
            return
        dialogo = ContraseniaDialog(
            "Restablecer contraseña",
            f"Contraseña nueva para \"{usuario['nombre_usuario']}\". La anterior deja de servir.",
            parent=self,
        )
        if not dialogo.exec():
            return
        try:
            repo.guardar_contrasenia(usuario["id"], dialogo.nueva)
        except Exception as e:
            theme.error_bd(self, e)
            return
        theme.informar(self, "Contraseña restablecida", "La contraseña nueva ya está en uso.")

    def _reactivar(self):
        usuario = self._seleccionado()
        if usuario is None:
            return
        if usuario["activo"]:
            theme.avisar(self, "Usuario activo", "Ese usuario ya está activo.")
            return
        try:
            repo.cambiar_activo(usuario["id"], True)
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar()

    def _eliminar(self):
        usuario = self._seleccionado()
        if usuario is None:
            return
        try:
            usuario_service.validar_baja(usuario, self.usuario_actual_id)
        except ValueError as e:
            theme.avisar(self, "No se puede eliminar", str(e))
            return
        nombre = usuario["nombre_usuario"]
        if usuario["con_historial"]:
            if not usuario["activo"]:
                theme.avisar(
                    self, "Usuario inactivo",
                    f"\"{nombre}\" ya está inactivo. No se borra porque cargó ausencias, "
                    "feriados o correcciones, y esos registros conservan su nombre.",
                )
                return
            pregunta = (
                f"\"{nombre}\" cargó ausencias, feriados o correcciones, así que no se borra: "
                "queda inactivo y ya no puede ingresar. ¿Desactivarlo?"
            )
        else:
            pregunta = f"¿Eliminar el usuario \"{nombre}\"?"
        if not theme.confirmar(self, "Eliminar usuario", pregunta):
            return
        try:
            if usuario["con_historial"]:
                repo.cambiar_activo(usuario["id"], False)
            else:
                repo.eliminar(usuario["id"])
        except Exception as e:
            theme.error_bd(self, e)
        self.refrescar()
