from utils.rutas import ruta_icono

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.usuario_service import (
    ErrorUsuario,
    ROLES_VALIDOS,
    actualizar_usuario,
    cambiar_estado,
    crear_usuario,
    listar_usuarios,
    restablecer_password,
)
from ui.estilos import ESTILO_GLOBAL


ROL_USUARIO_ID = int(Qt.ItemDataRole.UserRole)
ROL_ORDEN = ROL_USUARIO_ID + 1


ESTILO_USUARIOS = """
QPushButton#nuevo_usuario {
    background-color: #12aa52; color: white;
    border: 1px solid #0e9849; border-radius: 8px;
    padding: 9px 17px; font-size: 14px; font-weight: 900;
}
QPushButton#nuevo_usuario:hover { background-color: #0d9245; }
QPushButton#buscar_usuarios {
    background-color: #4da8da; color: white;
    border: 1px solid #3189b9; border-radius: 7px; font-weight: 800;
}
QPushButton#buscar_usuarios:hover { background-color: #3797cc; }
QPushButton#limpiar_usuarios, QPushButton#cancelar_usuario {
    background-color: #e2e8f0; color: #334155;
    border: 1px solid #cbd5e1; border-radius: 7px; font-weight: 700;
}
QPushButton#limpiar_usuarios:hover,
QPushButton#cancelar_usuario:hover { background-color: #d6dde6; }
QPushButton#guardar_usuario {
    background-color: #12aa52; color: white;
    border: 1px solid #0e9849; border-radius: 7px; font-weight: 900;
}
QPushButton#guardar_usuario:hover { background-color: #0d9245; }
QPushButton#editar_usuario {
    background-color: #887bd4; color: white;
    border: 1px solid #6e61bd; border-radius: 7px; font-weight: 800;
}
QPushButton#editar_usuario:hover { background-color: #7568c5; }
QPushButton#password_usuario {
    background-color: #f4d45e; color: #4f3b00;
    border: 1px solid #d8b83e; border-radius: 7px; font-weight: 800;
}
QPushButton#password_usuario:hover { background-color: #e9c845; }
QPushButton#activar_usuario {
    background-color: #55bf7a; color: white;
    border: 1px solid #3aa561; border-radius: 7px; font-weight: 800;
}
QPushButton#activar_usuario:hover { background-color: #42ae68; }
QPushButton#desactivar_usuario {
    background-color: #f08a7c; color: #5f2118;
    border: 1px solid #dd7466; border-radius: 7px; font-weight: 800;
}
QPushButton#desactivar_usuario:hover { background-color: #e77969; }
QPushButton#mostrar_password {
    background-color: #f8fafc; color: #475569;
    border: 1px solid #cbd5e1; border-radius: 7px; font-weight: 700;
}
QPushButton#mostrar_password:checked {
    background-color: #e5f7ec; color: #08783a; border-color: #55bf7a;
}
QPushButton#editar_usuario:disabled,
QPushButton#password_usuario:disabled,
QPushButton#activar_usuario:disabled,
QPushButton#desactivar_usuario:disabled {
    background-color: #e5e7eb; color: #9ca3af; border-color: #d4d8de;
}
QLabel#estado_usuario_activo {
    background-color: #e5f7ec; color: #08783a;
    border: 1px solid #a8dfbd; border-radius: 10px;
    padding: 3px 9px; font-weight: 800;
}
QLabel#estado_usuario_inactivo {
    background-color: #fff1f0; color: #b42318;
    border: 1px solid #efb4ae; border-radius: 10px;
    padding: 3px 9px; font-weight: 800;
}
"""


class ItemOrdenable(QTableWidgetItem):
    def __init__(self, texto, valor_orden=None):
        super().__init__(str(texto))
        self.setData(
            ROL_ORDEN,
            valor_orden if valor_orden is not None else str(texto).casefold(),
        )

    def __lt__(self, otro):
        propio = self.data(ROL_ORDEN)
        ajeno = otro.data(ROL_ORDEN)
        try:
            return propio < ajeno
        except TypeError:
            return str(propio).casefold() < str(ajeno).casefold()


class DialogoRestablecerPassword(QDialog):
    def __init__(self, nombre_usuario, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Restablecer contraseña")
        self.setModal(True)
        self.setMinimumWidth(470)
        self.setStyleSheet(ESTILO_GLOBAL + ESTILO_USUARIOS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        titulo = QLabel("RESTABLECER CONTRASEÑA")
        titulo.setObjectName("titulo_modulo")
        layout.addWidget(titulo)
        layout.addWidget(QLabel(f"Usuario: <b>{nombre_usuario}</b>"))

        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText("Nueva contraseña")
        self.campo_confirmacion = QLineEdit()
        self.campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_confirmacion.setPlaceholderText("Confirmar contraseña")
        layout.addWidget(QLabel("Nueva contraseña"))
        layout.addWidget(self.campo_password)
        layout.addWidget(QLabel("Confirmación"))
        layout.addWidget(self.campo_confirmacion)

        mostrar = QPushButton("○  Mostrar contraseñas")
        mostrar.setObjectName("mostrar_password")
        mostrar.setCheckable(True)
        mostrar.toggled.connect(
            lambda visible: self._mostrar_passwords(mostrar, visible)
        )
        layout.addWidget(mostrar)

        requisitos = QLabel(
            "Mínimo 6 caracteres, con al menos una letra y un número."
        )
        requisitos.setObjectName("subtitulo")
        layout.addWidget(requisitos)

        botones = QHBoxLayout()
        botones.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("cancelar_usuario")
        cancelar.clicked.connect(self.reject)
        aceptar = QPushButton("Guardar contraseña")
        aceptar.setObjectName("guardar_usuario")
        aceptar.clicked.connect(self._aceptar)
        botones.addWidget(cancelar)
        botones.addWidget(aceptar)
        layout.addLayout(botones)

    def _mostrar_passwords(self, boton, visible):
        modo = (
            QLineEdit.EchoMode.Normal
            if visible
            else QLineEdit.EchoMode.Password
        )
        self.campo_password.setEchoMode(modo)
        self.campo_confirmacion.setEchoMode(modo)
        boton.setText(
            "✓  Ocultar contraseñas" if visible else "○  Mostrar contraseñas"
        )

    def _aceptar(self):
        if not self.campo_password.text() or not self.campo_confirmacion.text():
            QMessageBox.warning(
                self,
                "Datos incompletos",
                "Completá y confirmá la nueva contraseña.",
            )
            return
        self.accept()


class VentanaUsuarios(QWidget):
    def __init__(self, usuario_actual):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.usuarios = []
        self.usuarios_por_id = {}
        self.usuario_editado_id = None

        self.setWindowTitle("NEPOS — Usuarios")
        self.resize(1050, 720)
        self.setStyleSheet(ESTILO_GLOBAL + ESTILO_USUARIOS)

        self._armar_interfaz()
        self.buscar()

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(self._crear_cabecera())
        layout.addWidget(self._crear_filtros())
        layout.addWidget(self._crear_formulario())
        layout.addWidget(self._crear_tabla(), 1)
        layout.addLayout(self._crear_acciones())

    def _crear_cabecera(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        fila = QHBoxLayout(tarjeta)
        fila.setContentsMargins(18, 10, 18, 10)
        fila.setSpacing(11)

        icono = QLabel()
        pixmap = QPixmap(str(ruta_icono("usuarios.png")))
        if not pixmap.isNull():
            icono.setPixmap(
                pixmap.scaled(
                    34,
                    34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            icono.setText("♙")
            icono.setStyleSheet("font-size:28px; color:#887bd4;")
        icono.setFixedSize(40, 40)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        textos = QVBoxLayout()
        textos.setSpacing(1)
        titulo = QLabel("USUARIOS")
        titulo.setObjectName("titulo_modulo")
        subtitulo = QLabel(
            "Administración segura de operadores, roles y accesos."
        )
        subtitulo.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        self.boton_nuevo = QPushButton("NUEVO USUARIO")
        self.boton_nuevo.setObjectName("nuevo_usuario")
        self.boton_nuevo.setMinimumSize(190, 44)
        self.boton_nuevo.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        self.boton_nuevo.setIconSize(QSize(22, 22))
        self.boton_nuevo.clicked.connect(self.nuevo_usuario)

        fila.addWidget(icono)
        fila.addLayout(textos)
        fila.addStretch()
        fila.addWidget(self.boton_nuevo)
        return tarjeta

    def _crear_filtros(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        fila = QHBoxLayout(tarjeta)
        fila.setContentsMargins(12, 9, 12, 9)
        fila.setSpacing(8)

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar por usuario o nombre")
        self.campo_busqueda.setMinimumHeight(40)
        self.campo_busqueda.returnPressed.connect(self.buscar)
        self.combo_rol_filtro = QComboBox()
        self.combo_rol_filtro.addItem("Todos los roles", None)
        for rol in ROLES_VALIDOS:
            self.combo_rol_filtro.addItem(rol, rol)
        self.combo_estado_filtro = QComboBox()
        self.combo_estado_filtro.addItems(["TODOS", "ACTIVOS", "INACTIVOS"])

        buscar = QPushButton("BUSCAR")
        buscar.setObjectName("buscar_usuarios")
        buscar.setMinimumHeight(40)
        buscar.clicked.connect(self.buscar)
        limpiar = QPushButton("LIMPIAR FILTROS")
        limpiar.setObjectName("limpiar_usuarios")
        limpiar.setMinimumHeight(40)
        limpiar.clicked.connect(self.limpiar_filtros)

        fila.addWidget(self.campo_busqueda, 2)
        fila.addWidget(self.combo_rol_filtro)
        fila.addWidget(self.combo_estado_filtro)
        fila.addWidget(buscar)
        fila.addWidget(limpiar)
        return tarjeta

    def _crear_formulario(self):
        self.formulario = QFrame()
        self.formulario.setObjectName("tarjeta")
        layout = QVBoxLayout(self.formulario)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        self.titulo_formulario = QLabel("NUEVO USUARIO")
        self.titulo_formulario.setStyleSheet(
            "font-size:14px; font-weight:900; color:#172033;"
        )
        layout.addWidget(self.titulo_formulario)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(5)
        self.campo_usuario = QLineEdit()
        self.campo_usuario.setPlaceholderText("Ej.: cajero_01")
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre y apellido")
        self.combo_rol = QComboBox()
        roles = ROLES_VALIDOS if self.usuario_actual.rol == "ADMIN" else ("CAJERO",)
        self.combo_rol.addItems(list(roles))
        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText("Mínimo 6 caracteres")
        self.campo_confirmacion = QLineEdit()
        self.campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_confirmacion.setPlaceholderText("Repetir contraseña")

        grid.addWidget(QLabel("Usuario"), 0, 0)
        grid.addWidget(self.campo_usuario, 1, 0)
        grid.addWidget(QLabel("Nombre"), 0, 1)
        grid.addWidget(self.campo_nombre, 1, 1)
        grid.addWidget(QLabel("Rol"), 0, 2)
        grid.addWidget(self.combo_rol, 1, 2)
        self.etiqueta_password = QLabel("Contraseña")
        self.etiqueta_confirmacion = QLabel("Confirmación")
        grid.addWidget(self.etiqueta_password, 2, 0)
        grid.addWidget(self.campo_password, 3, 0)
        grid.addWidget(self.etiqueta_confirmacion, 2, 1)
        grid.addWidget(self.campo_confirmacion, 3, 1)

        self.boton_mostrar = QPushButton("○  Mostrar contraseñas")
        self.boton_mostrar.setObjectName("mostrar_password")
        self.boton_mostrar.setCheckable(True)
        self.boton_mostrar.toggled.connect(self._mostrar_passwords)
        grid.addWidget(self.boton_mostrar, 3, 2)
        for columna in range(3):
            grid.setColumnStretch(columna, 1)
        layout.addLayout(grid)

        acciones = QHBoxLayout()
        acciones.addStretch()
        cancelar = QPushButton("CANCELAR")
        cancelar.setObjectName("cancelar_usuario")
        cancelar.clicked.connect(self.cancelar_formulario)
        self.boton_guardar = QPushButton("CREAR USUARIO")
        self.boton_guardar.setObjectName("guardar_usuario")
        self.boton_guardar.clicked.connect(self.guardar)
        acciones.addWidget(cancelar)
        acciones.addWidget(self.boton_guardar)
        layout.addLayout(acciones)

        self.formulario.setVisible(False)
        return self.formulario

    def _crear_tabla(self):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(6)
        encabezado = QHBoxLayout()
        encabezado.addWidget(QLabel("<b>USUARIOS EXISTENTES</b>"))
        encabezado.addStretch()
        self.etiqueta_resultados = QLabel("0 usuarios")
        self.etiqueta_resultados.setObjectName("subtitulo")
        encabezado.addWidget(self.etiqueta_resultados)
        layout.addLayout(encabezado)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["USUARIO", "NOMBRE", "ROL", "ESTADO", "CREADO", "ÚLTIMO ACCESO"]
        )
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(36)
        self.tabla.setSortingEnabled(True)
        header = self.tabla.horizontalHeader()
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.itemSelectionChanged.connect(self._actualizar_acciones)
        self.tabla.cellDoubleClicked.connect(lambda _f, _c: self.editar_seleccionado())
        layout.addWidget(self.tabla, 1)
        return tarjeta

    def _crear_acciones(self):
        fila = QHBoxLayout()
        fila.addWidget(QLabel("Seleccioná una fila para administrar la cuenta."))
        fila.addStretch()
        self.boton_editar = QPushButton("EDITAR")
        self.boton_editar.setObjectName("editar_usuario")
        self.boton_editar.clicked.connect(self.editar_seleccionado)
        self.boton_password = QPushButton("RESTABLECER CONTRASEÑA")
        self.boton_password.setObjectName("password_usuario")
        self.boton_password.clicked.connect(self.restablecer_password_seleccionado)
        self.boton_estado = QPushButton("ACTIVAR / DESACTIVAR")
        self.boton_estado.setObjectName("desactivar_usuario")
        self.boton_estado.clicked.connect(self.alternar_estado)
        fila.addWidget(self.boton_editar)
        fila.addWidget(self.boton_password)
        fila.addWidget(self.boton_estado)
        self._actualizar_acciones()
        return fila

    def limpiar_filtros(self):
        self.campo_busqueda.clear()
        self.combo_rol_filtro.setCurrentIndex(0)
        self.combo_estado_filtro.setCurrentText("TODOS")
        self.buscar()

    def buscar(self):
        try:
            usuarios = listar_usuarios(
                self.usuario_actual.id,
                busqueda=self.campo_busqueda.text(),
                rol=self.combo_rol_filtro.currentData(),
                estado=self.combo_estado_filtro.currentText(),
            )
        except ErrorUsuario as error:
            QMessageBox.warning(self, "Sin permiso", str(error))
            return
        self.usuarios = usuarios
        self.usuarios_por_id = {usuario.id: usuario for usuario in usuarios}
        sorting = self.tabla.isSortingEnabled()
        self.tabla.setSortingEnabled(False)
        self.tabla.clearContents()
        self.tabla.setRowCount(len(usuarios))
        for fila, usuario in enumerate(usuarios):
            creado = self._fecha_texto(getattr(usuario, "fecha_creacion", None))
            acceso = self._fecha_texto(getattr(usuario, "ultimo_acceso", None))
            valores = [
                (usuario.usuario, usuario.usuario.casefold()),
                (usuario.nombre or "", (usuario.nombre or "").casefold()),
                (
                    "ADMIN · SOPORTE NEPOS"
                    if getattr(usuario, "es_soporte", False)
                    else (usuario.rol or ""),
                    usuario.rol or "",
                ),
                ("Activo" if usuario.activo else "Inactivo", 0 if usuario.activo else 1),
                (creado, getattr(usuario, "fecha_creacion", None) or ""),
                (acceso, getattr(usuario, "ultimo_acceso", None) or ""),
            ]
            for columna, (texto, orden) in enumerate(valores):
                item = ItemOrdenable(texto, orden)
                item.setData(ROL_USUARIO_ID, usuario.id)
                if columna == 3:
                    item.setForeground(
                        QColor("#15803d" if usuario.activo else "#b91c1c")
                    )
                if getattr(usuario, "protegido", False):
                    item.setToolTip(
                        "Cuenta técnica protegida. Sus cambios se realizan "
                        "con el instalador local de NEPOS."
                    )
                self.tabla.setItem(fila, columna, item)
        self.tabla.setSortingEnabled(sorting)
        self.tabla.clearSelection()
        self.etiqueta_resultados.setText(f"{len(usuarios)} usuario(s)")
        self._actualizar_acciones()

    @staticmethod
    def _fecha_texto(valor):
        return valor.strftime("%d/%m/%Y %H:%M") if valor else "—"

    def _usuario_seleccionado(self, aviso=True):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            if aviso:
                QMessageBox.information(
                    self,
                    "Elegí un usuario",
                    "Seleccioná una fila de la tabla.",
                )
            return None
        item = self.tabla.item(filas[0].row(), 0)
        return self.usuarios_por_id.get(item.data(ROL_USUARIO_ID)) if item else None

    def _puede_gestionar(self, usuario):
        if not usuario:
            return False
        if getattr(usuario, "protegido", False):
            return False
        return self.usuario_actual.rol == "ADMIN" or usuario.rol == "CAJERO"

    def _actualizar_acciones(self):
        if not hasattr(self, "boton_editar"):
            return
        usuario = self._usuario_seleccionado(aviso=False)
        permitido = self._puede_gestionar(usuario)
        self.boton_editar.setEnabled(permitido)
        self.boton_password.setEnabled(permitido)
        puede_estado = permitido and usuario.id != self.usuario_actual.id if usuario else False
        self.boton_estado.setEnabled(puede_estado)
        activo = bool(usuario.activo) if usuario else True
        self.boton_estado.setText(
            "DESACTIVAR USUARIO" if activo else "ACTIVAR USUARIO"
        )
        self.boton_estado.setObjectName(
            "desactivar_usuario" if activo else "activar_usuario"
        )
        estilo = self.boton_estado.style()
        estilo.unpolish(self.boton_estado)
        estilo.polish(self.boton_estado)

    def nuevo_usuario(self):
        self.usuario_editado_id = None
        self._limpiar_formulario()
        self._mostrar_campos_password(True)
        self.titulo_formulario.setText("NUEVO USUARIO")
        self.boton_guardar.setText("CREAR USUARIO")
        self.formulario.setVisible(True)
        self.campo_usuario.setFocus()

    def editar_seleccionado(self):
        usuario = self._usuario_seleccionado()
        if not self._puede_gestionar(usuario):
            return
        self.usuario_editado_id = usuario.id
        self.campo_usuario.setText(usuario.usuario)
        self.campo_nombre.setText(usuario.nombre or "")
        indice = self.combo_rol.findText(usuario.rol)
        self.combo_rol.setCurrentIndex(max(indice, 0))
        self._mostrar_campos_password(False)
        self.titulo_formulario.setText(f"EDITAR USUARIO · {usuario.usuario}")
        self.boton_guardar.setText("GUARDAR CAMBIOS")
        self.formulario.setVisible(True)
        self.campo_nombre.setFocus()

    def _mostrar_campos_password(self, mostrar):
        for control in (
            self.etiqueta_password,
            self.campo_password,
            self.etiqueta_confirmacion,
            self.campo_confirmacion,
            self.boton_mostrar,
        ):
            control.setVisible(mostrar)

    def _mostrar_passwords(self, visible):
        modo = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        self.campo_password.setEchoMode(modo)
        self.campo_confirmacion.setEchoMode(modo)
        self.boton_mostrar.setText(
            "✓  Ocultar contraseñas" if visible else "○  Mostrar contraseñas"
        )

    def _limpiar_formulario(self):
        self.campo_usuario.clear()
        self.campo_nombre.clear()
        self.campo_password.clear()
        self.campo_confirmacion.clear()
        self.combo_rol.setCurrentIndex(0)
        self.boton_mostrar.setChecked(False)

    def cancelar_formulario(self):
        self.usuario_editado_id = None
        self._limpiar_formulario()
        self.formulario.setVisible(False)

    def guardar(self):
        try:
            if self.usuario_editado_id is None:
                crear_usuario(
                    usuario=self.campo_usuario.text(),
                    nombre=self.campo_nombre.text(),
                    password=self.campo_password.text(),
                    confirmar_password=self.campo_confirmacion.text(),
                    rol=self.combo_rol.currentText(),
                    solicitante_id=self.usuario_actual.id,
                )
                mensaje = "El usuario se creó correctamente."
            else:
                actualizar_usuario(
                    self.usuario_editado_id,
                    usuario=self.campo_usuario.text(),
                    nombre=self.campo_nombre.text(),
                    rol=self.combo_rol.currentText(),
                    solicitante_id=self.usuario_actual.id,
                )
                mensaje = "Los cambios se guardaron correctamente."
        except ErrorUsuario as error:
            QMessageBox.warning(self, "No se pudo guardar", str(error))
            return
        QMessageBox.information(self, "Usuario guardado", mensaje)
        self.cancelar_formulario()
        self.buscar()

    def restablecer_password_seleccionado(self):
        usuario = self._usuario_seleccionado()
        if not self._puede_gestionar(usuario):
            return
        dialogo = DialogoRestablecerPassword(usuario.usuario, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            restablecer_password(
                usuario.id,
                dialogo.campo_password.text(),
                dialogo.campo_confirmacion.text(),
                self.usuario_actual.id,
            )
        except ErrorUsuario as error:
            QMessageBox.warning(self, "No se pudo restablecer", str(error))
            return
        QMessageBox.information(
            self,
            "Contraseña actualizada",
            f"Se actualizó la contraseña de {usuario.usuario}.",
        )

    def alternar_estado(self):
        usuario = self._usuario_seleccionado()
        if not self._puede_gestionar(usuario):
            return
        activar = not bool(usuario.activo)
        accion = "activar" if activar else "desactivar"
        respuesta = QMessageBox.question(
            self,
            f"Confirmar {accion}",
            f"¿Querés {accion} la cuenta “{usuario.usuario}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            cambiar_estado(usuario.id, activar, self.usuario_actual.id)
        except ErrorUsuario as error:
            QMessageBox.warning(self, "No se pudo actualizar", str(error))
            return
        self.buscar()