from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QPushButton,
    QLabel, QMessageBox, QComboBox, QHBoxLayout,
)
from services.configuracion_service import (
    actualizar_configuracion_caja,
    actualizar_configuracion_comercio,
    actualizar_valor,
)
from services.impresion_service import (
    ErrorImpresion,
    imprimir_prueba,
    listar_impresoras,
)


class DialogoConfiguracionInicial(QDialog):
    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("Configuración inicial de NEPOS")
        self.setModal(True)
        self.resize(540, 650)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "<h3>Bienvenido a NEPOS</h3>"
            "<p>Antes de empezar, configurá los valores de tu negocio. "
            "Podés cambiarlos después desde Configuración.</p>"
        ))

        form = QFormLayout()
        self.campo_nombre_comercio = QLineEdit()
        self.campo_nombre_comercio.setPlaceholderText("Nombre que aparecerá en el ticket")
        self.campo_direccion = QLineEdit()
        self.campo_telefono = QLineEdit()
        self.campo_cuit = QLineEdit()
        self.campo_cuit.setPlaceholderText("XX-XXXXXXXX-X")
        self.combo_impresora = QComboBox()
        self.combo_impresora.addItem("Sin impresora por ahora", "")
        try:
            for nombre in listar_impresoras():
                self.combo_impresora.addItem(nombre, nombre)
        except ErrorImpresion:
            pass

        form.addRow("Nombre del comercio:", self.campo_nombre_comercio)
        form.addRow("Dirección:", self.campo_direccion)
        form.addRow("Teléfono:", self.campo_telefono)
        form.addRow("CUIT:", self.campo_cuit)
        form.addRow("Impresora térmica:", self.combo_impresora)

        self.campo_iva = QLineEdit("21")
        self.campo_iva.setReadOnly(True)
        self.campo_iva.setToolTip(
            "Carnicería y Panadería usan 10,5%; las demás categorías, 21%."
        )
        self.campo_recargo_cigarrillos = QLineEdit("15")
        self.campo_recargo_credito = QLineEdit("15")
        self.campo_redondeo = QLineEdit("2")
        self.check_stock_negativo = QCheckBox("Permitir vender sin stock disponible")
        self.check_stock_negativo.setChecked(True)

        form.addRow("IVA general (%):", self.campo_iva)
        form.addRow(
            "",
            QLabel("Carnicería y Panadería se registran automáticamente al 10,5%."),
        )
        form.addRow("Recargo cigarrillos (%):", self.campo_recargo_cigarrillos)
        form.addRow("Recargo crédito (%):", self.campo_recargo_credito)
        form.addRow("Redondeo (decimales):", self.campo_redondeo)
        form.addRow("", self.check_stock_negativo)
        layout.addLayout(form)

        acciones = QHBoxLayout()
        boton_prueba = QPushButton("Probar impresora")
        boton_prueba.clicked.connect(self.probar_impresora)
        boton_guardar = QPushButton("Guardar y continuar")
        boton_guardar.setStyleSheet("font-weight: bold; padding: 8px;")
        boton_guardar.clicked.connect(self.guardar)
        acciones.addWidget(boton_prueba)
        acciones.addStretch()
        acciones.addWidget(boton_guardar)
        layout.addLayout(acciones)

    def probar_impresora(self):
        nombre = self.combo_impresora.currentData()
        if not nombre:
            QMessageBox.information(
                self,
                "Elegí una impresora",
                "Seleccioná una impresora instalada para hacer la prueba.",
            )
            return
        try:
            imprimir_prueba(
                nombre,
                {
                    "nombre": self.campo_nombre_comercio.text(),
                    "direccion": self.campo_direccion.text(),
                    "telefono": self.campo_telefono.text(),
                    "cuit": self.campo_cuit.text(),
                },
            )
        except ErrorImpresion as error:
            QMessageBox.warning(self, "No se pudo imprimir", str(error))
            return
        QMessageBox.information(self, "Prueba enviada", "Revisá la impresora.")

    def guardar(self):
        try:
            valores = {
                "iva_default": float(self.campo_iva.text().replace(",", ".")),
                "recargo_cigarrillos": float(self.campo_recargo_cigarrillos.text().replace(",", ".")) / 100,
                "recargo_credito": float(self.campo_recargo_credito.text().replace(",", ".")) / 100,
                "redondeo_decimales": int(self.campo_redondeo.text()),
                "medios_pago": ["EFECTIVO", "QR", "DEBITO", "CREDITO"],
                "permitir_stock_negativo": self.check_stock_negativo.isChecked(),
            }
        except ValueError:
            QMessageBox.warning(self, "Valores inválidos", "Revisá que los campos numéricos sean correctos.")
            return

        try:
            actualizar_configuracion_comercio(
                {
                    "nombre": self.campo_nombre_comercio.text(),
                    "direccion": self.campo_direccion.text(),
                    "telefono": self.campo_telefono.text(),
                    "cuit": self.campo_cuit.text(),
                    "impresora": self.combo_impresora.currentData(),
                },
                self.usuario.id,
            )
            actualizar_configuracion_caja(valores, self.usuario.id)
            actualizar_valor("CONFIGURACION_INICIAL_COMPLETA", "true", self.usuario.id)
        except (ValueError, PermissionError) as e:
            QMessageBox.warning(self, "No se pudo guardar", str(e))
            return

        self.accept()
