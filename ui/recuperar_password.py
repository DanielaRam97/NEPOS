from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.usuario_service import (
    ErrorUsuario,
    recuperar_password_con_admin,
)


ESTILO_CAMPO = """
QLineEdit {
    background: #ffffff;
    border: 1px solid #8b95a5;
    border-radius: 7px;
    color: #243047;
    font-size: 14px;
    padding: 11px 13px;
}
QLineEdit:focus {
    border: 2px solid #13aa52;
}
"""


class VentanaRecuperarPassword(QDialog):
    def __init__(self, usuario_inicial="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recuperar contraseña - NEPOS")
        self.setModal(True)
        self.setFixedSize(520, 650)
        self.setObjectName("ventana_recuperar")
        self.setStyleSheet("""
            QDialog#ventana_recuperar {
                background: #f7f8fa;
            }
            QDialog#ventana_recuperar QLabel {
                background: transparent;
            }
        """)

        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(14, 14, 14, 14)

        tarjeta = QFrame()
        tarjeta.setStyleSheet("QFrame { background: #f7f8fa; }")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(54, 34, 54, 38)
        layout.setSpacing(12)

        titulo = QLabel("N  E  P  O  S")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "color: #050505; font-size: 28px; font-weight: 900;"
        )
        subtitulo = QLabel("Recuperar contraseña")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet(
            "color: #334155; font-size: 16px; font-weight: 600;"
        )
        explicacion = QLabel(
            "Por seguridad, un usuario ADMIN debe autorizar el cambio."
        )
        explicacion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        explicacion.setWordWrap(True)
        explicacion.setStyleSheet("color: #64748b; font-size: 12px;")

        self.campo_usuario = self._crear_campo(
            "Usuario que recuperará la contraseña"
        )
        self.campo_usuario.setText(usuario_inicial)
        self.campo_nueva_password = self._crear_campo(
            "Nueva contraseña",
            password=True,
        )
        self.campo_confirmar_password = self._crear_campo(
            "Repetir nueva contraseña",
            password=True,
        )

        separador = QLabel("AUTORIZACIÓN DEL ADMINISTRADOR")
        separador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separador.setStyleSheet(
            "color: #475569; font-size: 11px; font-weight: 700; "
            "margin-top: 12px;"
        )

        self.campo_admin = self._crear_campo("Usuario administrador")
        self.campo_password_admin = self._crear_campo(
            "Contraseña del administrador",
            password=True,
        )

        self.etiqueta_error = QLabel("")
        self.etiqueta_error.setWordWrap(True)
        self.etiqueta_error.setStyleSheet(
            "color: #dc2626; font-size: 12px;"
        )

        boton_restablecer = QPushButton("R E S T A B L E C E R")
        boton_restablecer.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_restablecer.setStyleSheet("""
            QPushButton {
                background: #13aa52;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 13px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover { background: #0f9848; }
            QPushButton:pressed { background: #0b7f3b; }
        """)
        boton_restablecer.clicked.connect(self.restablecer)

        boton_volver = QPushButton("Volver al inicio de sesión")
        boton_volver.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_volver.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #13aa52;
                border: none;
                font-size: 13px;
                font-weight: 600;
                padding: 8px;
            }
            QPushButton:hover { color: #0b7f3b; }
        """)
        boton_volver.clicked.connect(self.reject)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        layout.addWidget(explicacion)
        layout.addSpacing(8)
        layout.addWidget(self.campo_usuario)
        layout.addWidget(self.campo_nueva_password)
        layout.addWidget(self.campo_confirmar_password)
        layout.addWidget(separador)
        layout.addWidget(self.campo_admin)
        layout.addWidget(self.campo_password_admin)
        layout.addWidget(self.etiqueta_error)
        layout.addStretch()
        layout.addWidget(boton_restablecer)
        layout.addWidget(boton_volver)
        exterior.addWidget(tarjeta)

        self.campo_password_admin.returnPressed.connect(self.restablecer)

    @staticmethod
    def _crear_campo(placeholder, password=False):
        campo = QLineEdit()
        campo.setPlaceholderText(placeholder)
        campo.setStyleSheet(ESTILO_CAMPO)
        campo.setMinimumHeight(46)
        if password:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
        return campo

    def restablecer(self):
        self.etiqueta_error.clear()
        try:
            usuario = recuperar_password_con_admin(
                usuario_objetivo=self.campo_usuario.text(),
                nueva_password=self.campo_nueva_password.text(),
                confirmar_password=self.campo_confirmar_password.text(),
                usuario_admin=self.campo_admin.text(),
                password_admin=self.campo_password_admin.text(),
            )
        except ErrorUsuario as error:
            self.etiqueta_error.setText(str(error))
            return
        except Exception as error:
            QMessageBox.critical(
                self,
                "No se pudo recuperar",
                f"Ocurrió un error al actualizar la contraseña:\n{error}",
            )
            return

        QMessageBox.information(
            self,
            "Contraseña actualizada",
            f"La contraseña de '{usuario}' se actualizó correctamente.",
        )
        self.accept()
