from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.usuario_service import ErrorUsuario, crear_usuario
from ui.estilos import ESTILO_GLOBAL


ESTILO_PRIMER_USUARIO = """
QPushButton#crear_primer_admin {
    background-color: #12aa52;
    color: #ffffff;
    border: 1px solid #0e9849;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 14px;
    font-weight: 900;
}
QPushButton#crear_primer_admin:hover {
    background-color: #0d9245;
}
QPushButton#crear_primer_admin:pressed {
    background-color: #087b3a;
}
QPushButton#mostrar_password_inicial {
    background-color: #f8fafc;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 7px 11px;
    font-weight: 700;
}
QPushButton#mostrar_password_inicial:checked {
    background-color: #e5f7ec;
    color: #08783a;
    border-color: #55bf7a;
}
"""


class DialogoPrimerUsuario(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración inicial — Crear administrador")
        self.setModal(True)
        self.setMinimumWidth(470)
        self.setStyleSheet(ESTILO_GLOBAL + ESTILO_PRIMER_USUARIO)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(12)

        titulo = QLabel("CONFIGURACIÓN INICIAL")
        titulo.setObjectName("titulo_modulo")
        layout.addWidget(titulo)

        descripcion = QLabel(
            "Todavía no hay usuarios. Creá la primera cuenta ADMIN para "
            "comenzar a usar NEPOS."
        )
        descripcion.setObjectName("subtitulo")
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        form = QFormLayout()
        form.setSpacing(10)
        self.campo_usuario = QLineEdit()
        self.campo_usuario.setPlaceholderText("Ej.: administrador")
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre completo")
        self.campo_password = QLineEdit()
        self.campo_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_password.setPlaceholderText("Mínimo 6 caracteres")
        self.campo_confirmar = QLineEdit()
        self.campo_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.campo_confirmar.setPlaceholderText("Repetir contraseña")

        form.addRow("Usuario:", self.campo_usuario)
        form.addRow("Nombre completo:", self.campo_nombre)
        form.addRow("Contraseña:", self.campo_password)
        form.addRow("Confirmación:", self.campo_confirmar)
        layout.addLayout(form)

        self.boton_mostrar = QPushButton("○  Mostrar contraseñas")
        self.boton_mostrar.setObjectName("mostrar_password_inicial")
        self.boton_mostrar.setCheckable(True)
        self.boton_mostrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_mostrar.toggled.connect(self._mostrar_passwords)
        layout.addWidget(self.boton_mostrar)

        requisitos = QLabel(
            "La contraseña debe tener al menos 6 caracteres, una letra y "
            "un número."
        )
        requisitos.setObjectName("subtitulo")
        requisitos.setWordWrap(True)
        layout.addWidget(requisitos)

        boton_crear = QPushButton("CREAR ADMINISTRADOR")
        boton_crear.setObjectName("crear_primer_admin")
        boton_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_crear.clicked.connect(self.crear)
        layout.addWidget(boton_crear)

        self.campo_confirmar.returnPressed.connect(self.crear)
        self.campo_usuario.setFocus()

    def _mostrar_passwords(self, visible):
        modo = (
            QLineEdit.EchoMode.Normal
            if visible
            else QLineEdit.EchoMode.Password
        )
        self.campo_password.setEchoMode(modo)
        self.campo_confirmar.setEchoMode(modo)
        self.boton_mostrar.setText(
            "✓  Ocultar contraseñas"
            if visible
            else "○  Mostrar contraseñas"
        )

    def crear(self):
        try:
            crear_usuario(
                usuario=self.campo_usuario.text(),
                nombre=self.campo_nombre.text(),
                password=self.campo_password.text(),
                confirmar_password=self.campo_confirmar.text(),
                rol="ADMIN",
            )
        except ErrorUsuario as error:
            QMessageBox.warning(self, "No se pudo crear", str(error))
            return

        QMessageBox.information(
            self,
            "Administrador creado",
            "La cuenta ADMIN se creó correctamente. Ya podés iniciar sesión.",
        )
        self.accept()