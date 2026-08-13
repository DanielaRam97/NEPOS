from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox
)
from services.turno_service import (
    abrir_turno,
    ErrorTurno,
    FONDO_INICIAL_DEFECTO,
    FONDO_INICIAL_MAXIMO,
)
from ui.estilos import configurar_boton_primario
from utils.formato import formatear_moneda
from utils.validacion import convertir_decimal_finito


class VentanaApertura(QWidget):
    def __init__(self, usuario, al_abrir_turno):
        super().__init__()
        self.usuario = usuario
        self.al_abrir_turno = al_abrir_turno

        self.setWindowTitle("NEPOS — Apertura de turno")
        self.setFixedSize(430, 300)

        self.combo_turno = QComboBox()
        self.combo_turno.addItems(["TURNO MAÑANA", "TURNO TARDE"])

        self.campo_fondo = QLineEdit(str(int(FONDO_INICIAL_DEFECTO)))
        self.campo_fondo.setValidator(
            QDoubleValidator(0, FONDO_INICIAL_MAXIMO, 2, self)
        )
        self.campo_fondo.setPlaceholderText("Ej.: 20000")

        formulario = QFormLayout()
        formulario.addRow("Turno:", self.combo_turno)
        formulario.addRow("Fondo inicial ($):", self.campo_fondo)

        boton_abrir = configurar_boton_primario(
            QPushButton("ABRIR TURNO")
        )
        boton_abrir.setMinimumHeight(42)
        boton_abrir.clicked.connect(self.abrir)

        self.etiqueta_error = QLabel("")
        self.etiqueta_error.setStyleSheet("color: red;")
        self.etiqueta_error.setWordWrap(True)

        layout = QVBoxLayout()
        titulo = QLabel("APERTURA DE TURNO")
        titulo.setObjectName("titulo_modulo")
        layout.addWidget(titulo)
        layout.addWidget(QLabel(f"Hola, {self.usuario.nombre}"))
        layout.addLayout(formulario)
        layout.addWidget(self.etiqueta_error)
        layout.addWidget(boton_abrir)
        self.setLayout(layout)

    def abrir(self):
        if not self.campo_fondo.text().strip():
            self.etiqueta_error.setText("Ingresá el fondo inicial de caja.")
            return

        try:
            fondo_inicial = convertir_decimal_finito(
                self.campo_fondo.text(),
                nombre="El fondo inicial",
                minimo=0,
                maximo=FONDO_INICIAL_MAXIMO,
                interpretar_punto_miles=True,
            )
        except ValueError as error:
            self.etiqueta_error.setText(str(error))
            return

        confirmacion = QMessageBox.question(
            self,
            "Confirmar apertura",
            f"Turno: {self.combo_turno.currentText()}\n"
            f"Fondo inicial: {formatear_moneda(fondo_inicial)}\n\n"
            "¿Los datos son correctos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirmacion != QMessageBox.StandardButton.Yes:
            return

        try:
            turno = abrir_turno(
                usuario_id=self.usuario.id,
                nombre_turno=self.combo_turno.currentText(),
                fondo_inicial=fondo_inicial,
            )
        except ErrorTurno as e:
            self.etiqueta_error.setText(str(e))
            return

        self.close()
        self.al_abrir_turno(turno)
