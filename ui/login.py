import bcrypt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database.conexion import nueva_sesion
from database.modelos import Usuario
from services.usuario_service import registrar_ultimo_acceso
from ui.recuperar_password import VentanaRecuperarPassword
from version import __version__


class VentanaLogin(QWidget):
    def __init__(self, al_loguear_exitosamente):
        super().__init__()
        self.al_loguear_exitosamente = al_loguear_exitosamente
        self.ventana_recuperar = None

        self.setWindowTitle(f"NEPOS {__version__} — Iniciar sesión")
        self.setFixedSize(570, 590)
        self.setObjectName("ventana_login")
        self.setStyleSheet("""
            QWidget#ventana_login {
                background-color: #f7f8fa;
                color: #172033;
            }
            QWidget#ventana_login QLabel {
                background: transparent;
                color: #172033;
            }
            QWidget#ventana_login QFrame#tarjeta {
                background-color: #ffffff;
                border: 1px solid #d8dde5;
                border-radius: 12px;
            }
        """)

        self._armar_interfaz()
        self.campo_usuario.setFocus()

    def _armar_interfaz(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(10, 10, 10, 14)
        exterior.setSpacing(7)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")
        tarjeta.setStyleSheet("""
            QFrame#tarjeta {
                background-color: #ffffff;
                border: 1px solid #d8dde5;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(62, 62, 62, 54)
        layout.setSpacing(14)

        logo = QLabel("N  E  P  O  S")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            "background: transparent; color: #050505; "
            "font-size: 36px; font-weight: 900;"
        )

        subtitulo = QLabel("Iniciá sesión para acceder a tu cuenta")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setStyleSheet(
            "background: transparent; color: #475569; font-size: 12px;"
        )

        contenedor_usuario, self.campo_usuario = self._crear_campo(
            icono="👤",
            placeholder="Ingresá tu usuario",
        )
        contenedor_password, self.campo_password = self._crear_campo(
            icono="🔒",
            placeholder="Ingresá tu contraseña",
            password=True,
        )

        boton_recuperar = QPushButton("¿Olvidaste tu contraseña?")
        boton_recuperar.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_recuperar.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #00a94f;
                font-size: 13px;
                font-weight: 700;
                padding: 6px;
            }
            QPushButton:hover {
                color: #087f3d;
                text-decoration: underline;
            }
        """)
        boton_recuperar.clicked.connect(self.abrir_recuperacion)

        self.etiqueta_error = QLabel("")
        self.etiqueta_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_error.setWordWrap(True)
        self.etiqueta_error.setStyleSheet(
            "background: transparent; color: #dc2626; "
            "font-size: 12px; font-weight: 600;"
        )

        boton_ingresar = QPushButton("I N I C I A R   S E S I Ó N")
        boton_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_ingresar.setMinimumHeight(44)
        boton_ingresar.setStyleSheet("""
            QPushButton {
                background: #13aa52;
                color: white;
                border: none;
                border-radius: 7px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover { background: #0f9848; }
            QPushButton:pressed { background: #0b7f3b; }
            QPushButton:disabled { background: #94d3ae; }
        """)
        boton_ingresar.clicked.connect(self.intentar_login)

        aviso = QLabel(
            "El alta de usuarios se realiza desde el módulo Usuarios "
            f"por un administrador. · Versión {__version__}"
        )
        aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        aviso.setWordWrap(True)
        aviso.setStyleSheet(
            "background: transparent; color: #64748b; font-size: 11px;"
        )

        layout.addWidget(logo)
        layout.addWidget(subtitulo)
        layout.addSpacing(18)
        layout.addWidget(contenedor_usuario)
        layout.addWidget(contenedor_password)
        layout.addWidget(boton_recuperar)
        layout.addWidget(self.etiqueta_error)
        layout.addWidget(boton_ingresar)
        layout.addStretch()
        layout.addWidget(aviso)
        exterior.addWidget(tarjeta)

        self.campo_usuario.returnPressed.connect(
            self.campo_password.setFocus
        )
        self.campo_password.returnPressed.connect(self.intentar_login)

    def _crear_campo(self, *, icono, placeholder, password=False):
        contenedor = QFrame()
        contenedor.setObjectName("campo")
        contenedor.setMinimumHeight(46)
        contenedor.setStyleSheet("""
            QFrame#campo {
                background: #ffffff;
                border: 1px solid #8792a2;
                border-radius: 7px;
            }
            QFrame#campo:focus-within {
                border: 2px solid #13aa52;
            }
        """)

        fila = QHBoxLayout(contenedor)
        fila.setContentsMargins(0, 0, 6, 0)
        fila.setSpacing(0)

        etiqueta_icono = QLabel(icono)
        etiqueta_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        etiqueta_icono.setFixedWidth(42)
        etiqueta_icono.setStyleSheet("""
            color: #0f9b46;
            background: transparent;
            border-right: 1px solid #aab2bf;
            font-size: 16px;
            font-weight: 700;
        """)

        campo = QLineEdit()
        campo.setPlaceholderText(placeholder)
        campo.setMinimumHeight(43)
        campo.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #253047;
                font-size: 14px;
                padding: 0 11px;
            }
        """)

        fila.addWidget(etiqueta_icono)
        fila.addWidget(campo, 1)

        if password:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            boton_ver = QPushButton("◉")
            boton_ver.setCheckable(True)
            boton_ver.setToolTip("Mostrar u ocultar contraseña")
            boton_ver.setCursor(Qt.CursorShape.PointingHandCursor)
            boton_ver.setFixedSize(30, 30)
            boton_ver.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: #253047;
                    font-size: 16px;
                }
                QPushButton:hover { color: #00a94f; }
            """)
            boton_ver.toggled.connect(
                lambda visible: campo.setEchoMode(
                    QLineEdit.EchoMode.Normal
                    if visible
                    else QLineEdit.EchoMode.Password
                )
            )
            fila.addWidget(boton_ver)

        return contenedor, campo

    def abrir_recuperacion(self):
        self.ventana_recuperar = VentanaRecuperarPassword(
            self.campo_usuario.text().strip(),
            self,
        )
        if self.ventana_recuperar.exec():
            self.campo_usuario.setText(
                self.ventana_recuperar.campo_usuario.text().strip()
            )
            self.campo_password.clear()
            self.etiqueta_error.clear()
            self.campo_password.setFocus()

    def intentar_login(self):
        nombre_usuario = self.campo_usuario.text().strip()
        password = self.campo_password.text()
        self.etiqueta_error.clear()

        if not nombre_usuario or not password:
            self.etiqueta_error.setText(
                "Completá el usuario y la contraseña."
            )
            return

        db = nueva_sesion()
        try:
            usuario = (
                db.query(Usuario)
                .filter(Usuario.usuario == nombre_usuario)
                .first()
            )

            if not usuario or not usuario.activo:
                self.etiqueta_error.setText(
                    "Usuario inexistente o inactivo."
                )
                return

            try:
                password_correcta = bcrypt.checkpw(
                    password.encode(),
                    usuario.password_hash.encode(),
                )
            except ValueError:
                password_correcta = False

            if not password_correcta:
                self.etiqueta_error.setText("Contraseña incorrecta.")
                self.campo_password.selectAll()
                self.campo_password.setFocus()
                return

            usuario_id = usuario.id
            db.expunge(usuario)
        except Exception as error:
            self.etiqueta_error.setText(
                f"No se pudo iniciar sesión: {error}"
            )
            return
        finally:
            db.close()

        try:
            registrar_ultimo_acceso(usuario_id)
        except Exception as error:
            self.etiqueta_error.setText(
                f"No se pudo registrar el acceso: {error}"
            )
            return

        self.close()
        self.al_loguear_exitosamente(usuario)
