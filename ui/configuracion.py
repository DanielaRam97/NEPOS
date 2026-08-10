from datetime import date, timedelta

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QComboBox,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
)

from services.configuracion_service import (
    obtener_configuracion_caja,
    obtener_configuracion_comercio,
    actualizar_configuracion_caja,
    actualizar_configuracion_comercio,
)
from services.impresion_service import (
    ErrorImpresion,
    imprimir_prueba,
    listar_impresoras,
)
from services.historial_service import listar_ventas
from services.exportar_service import (
    exportar_ventas_excel,
    exportar_ventas_pdf,
)
from utils.rutas import directorio_datos, ruta_configuracion

OPCIONES_PERIODO = [
    "Hoy",
    "Esta semana",
    "Este mes",
    "Todo el historial",
]


class VentanaConfiguracion(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario

        self.setObjectName("pagina_configuracion")

        self._armar_interfaz()
        self._cargar_valores()

    def _armar_interfaz(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("scroll_configuracion")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        contenido = QWidget()
        contenido.setObjectName("contenido_configuracion")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(18, 12, 18, 18)
        layout.setSpacing(10)

        titulo = QLabel("⚙  CONFIGURACIÓN")
        titulo.setObjectName("titulo_modulo")
        layout.addWidget(titulo)
        subtitulo = QLabel(
            "Datos del comercio, impresión, reglas de caja y exportaciones."
        )
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(subtitulo)

        ubicacion = QLabel(
            f"Datos permanentes: {directorio_datos()}\n"
            f"Conexión local: {ruta_configuracion()}"
        )
        ubicacion.setWordWrap(True)
        ubicacion.setStyleSheet(
            "background:#eef2f6; color:#475569; border:1px solid #cbd5e1; "
            "border-radius:7px; padding:8px;"
        )
        layout.addWidget(ubicacion)
        boton_abrir_datos = QPushButton("Abrir carpeta de datos de NEPOS")
        boton_abrir_datos.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(directorio_datos()))
            )
        )
        layout.addWidget(boton_abrir_datos)

        layout.addWidget(QLabel("<h3>Datos del comercio y ticket</h3>"))

        form = QFormLayout()

        self.campo_nombre_comercio = QLineEdit()
        self.campo_direccion = QLineEdit()
        self.campo_telefono = QLineEdit()
        self.campo_cuit = QLineEdit()
        self.combo_impresora = QComboBox()
        self.combo_impresora.addItem("Sin impresora configurada", "")
        try:
            for nombre in listar_impresoras():
                self.combo_impresora.addItem(nombre, nombre)
        except ErrorImpresion:
            pass
        form.addRow("Nombre:", self.campo_nombre_comercio)
        form.addRow("Dirección:", self.campo_direccion)
        form.addRow("Teléfono:", self.campo_telefono)
        form.addRow("CUIT:", self.campo_cuit)
        form.addRow("Impresora:", self.combo_impresora)
        boton_prueba = QPushButton("Enviar impresión de prueba")
        boton_prueba.clicked.connect(self.probar_impresora)
        form.addRow("", boton_prueba)

        layout.addLayout(form)
        layout.addWidget(QLabel("<h3>Configuración de Caja</h3>"))

        form = QFormLayout()

        self.campo_cigarrillos = QLineEdit()
        self.campo_credito = QLineEdit()
        self.campo_redondeo = QLineEdit()
        self.campo_iva_default = QLineEdit()
        self.campo_iva_default.setReadOnly(True)
        self.campo_iva_default.setToolTip(
            "Carnicería y Panadería usan 10,5%; las demás categorías, 21%."
        )

        self.check_permitir_stock_negativo = QCheckBox(
            "Permitir vender sin stock disponible"
        )

        form.addRow("Recargo cigarrillos (%):", self.campo_cigarrillos)
        form.addRow("Recargo crédito (%):", self.campo_credito)
        form.addRow("Redondeo (decimales):", self.campo_redondeo)
        form.addRow("IVA general (%):", self.campo_iva_default)
        form.addRow(
            "",
            QLabel("Carnicería y Panadería se registran automáticamente al 10,5%."),
        )
        form.addRow("", self.check_permitir_stock_negativo)

        layout.addLayout(form)

        # ----------- ESTE BLOQUE ES DEL PRIMER CÓDIGO -----------
        layout.addWidget(
            QLabel(
                "<small>"
                "Medios de pago habilitados: se administran junto con el "
                "resto del equipo (no editable desde acá todavía)."
                "</small>"
            )
        )
        # --------------------------------------------------------

        boton_guardar = QPushButton("Guardar")
        boton_guardar.setStyleSheet(
            "font-weight: bold; padding: 6px;"
        )
        boton_guardar.clicked.connect(self.guardar)

        layout.addWidget(boton_guardar)

        # ======================================================
        # EXPORTACIÓN
        # ======================================================

        layout.addWidget(QLabel("<hr><h3>Exportar reportes</h3>"))

        fila_periodo = QHBoxLayout()

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(OPCIONES_PERIODO)

        fila_periodo.addWidget(QLabel("Período:"))
        fila_periodo.addWidget(self.combo_periodo)

        layout.addLayout(fila_periodo)

        fila_botones = QHBoxLayout()

        boton_excel = QPushButton("Exportar a Excel")
        boton_excel.clicked.connect(self.exportar_excel)

        boton_pdf = QPushButton("Exportar a PDF")
        boton_pdf.clicked.connect(self.exportar_pdf)

        fila_botones.addWidget(boton_excel)
        fila_botones.addWidget(boton_pdf)

        layout.addLayout(fila_botones)

        layout.addStretch()
        scroll.setWidget(contenido)
        exterior.addWidget(scroll)

    def _cargar_valores(self):
        config = obtener_configuracion_caja()
        comercio = obtener_configuracion_comercio()

        self.campo_nombre_comercio.setText(comercio["nombre"])
        self.campo_direccion.setText(comercio["direccion"])
        self.campo_telefono.setText(comercio["telefono"])
        self.campo_cuit.setText(comercio["cuit"])
        indice = self.combo_impresora.findData(comercio["impresora"])
        if indice < 0 and comercio["impresora"]:
            self.combo_impresora.addItem(
                comercio["impresora"],
                comercio["impresora"],
            )
            indice = self.combo_impresora.count() - 1
        self.combo_impresora.setCurrentIndex(max(indice, 0))

        self.campo_cigarrillos.setText(
            str(round(config["recargo_cigarrillos"] * 100, 2))
        )
        self.campo_credito.setText(
            str(round(config["recargo_credito"] * 100, 2))
        )
        self.campo_redondeo.setText(
            str(config["redondeo_decimales"])
        )
        self.campo_iva_default.setText(
            str(config["iva_default"])
        )

        self.check_permitir_stock_negativo.setChecked(
            config["permitir_stock_negativo"]
        )

        self._medios_pago_actuales = config["medios_pago"]

    def refrescar(self):
        """Actualiza los campos cada vez que se abre la pestaña."""
        self._cargar_valores()

    def guardar(self):
        try:
            valores = {
                "recargo_cigarrillos": float(
                    self.campo_cigarrillos.text().replace(",", ".")
                ) / 100,
                "recargo_credito": float(
                    self.campo_credito.text().replace(",", ".")
                ) / 100,
                "redondeo_decimales": int(
                    self.campo_redondeo.text()
                ),
                "iva_default": float(
                    self.campo_iva_default.text().replace(",", ".")
                ),
                "medios_pago": self._medios_pago_actuales,
                "permitir_stock_negativo": self.check_permitir_stock_negativo.isChecked(),
            }

        except ValueError:
            QMessageBox.warning(
                self,
                "Valores inválidos",
                "Revisá que los campos numéricos sean correctos.",
            )
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
            actualizar_configuracion_caja(
                valores,
                self.usuario.id,
            )

        except (ValueError, PermissionError) as e:
            QMessageBox.warning(
                self,
                "No se pudo guardar",
                str(e),
            )
            return

        QMessageBox.information(
            self,
            "Guardado",
            "La configuración se actualizó correctamente.",
        )

    def probar_impresora(self):
        nombre = self.combo_impresora.currentData()
        if not nombre:
            QMessageBox.information(
                self,
                "Elegí una impresora",
                "Seleccioná una impresora para hacer la prueba.",
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

    # ======================================================
    # EXPORTACIÓN
    # ======================================================

    def _rango_fechas(self):
        periodo = self.combo_periodo.currentText()
        hoy = date.today()

        if periodo == "Hoy":
            return hoy.isoformat(), hoy.isoformat()

        if periodo == "Esta semana":
            return (
                (hoy - timedelta(days=hoy.weekday())).isoformat(),
                hoy.isoformat(),
            )

        if periodo == "Este mes":
            return (
                hoy.replace(day=1).isoformat(),
                hoy.isoformat(),
            )

        return None, None

    def exportar_excel(self):
        desde, hasta = self._rango_fechas()

        ventas = listar_ventas(
            fecha_desde=desde,
            fecha_hasta=hasta,
        )

        if not ventas:
            QMessageBox.information(
                self,
                "Sin datos",
                "No hay ventas en ese período.",
            )
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            "reporte.xlsx",
            "Excel (*.xlsx)",
        )

        if not ruta:
            return

        try:
            exportar_ventas_excel(
                ventas,
                ruta,
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                str(e),
            )
            return

        QMessageBox.information(
            self,
            "Listo",
            f"Se exportó correctamente a:\n{ruta}",
        )

    def exportar_pdf(self):
        desde, hasta = self._rango_fechas()

        ventas = listar_ventas(
            fecha_desde=desde,
            fecha_hasta=hasta,
        )

        if not ventas:
            QMessageBox.information(
                self,
                "Sin datos",
                "No hay ventas en ese período.",
            )
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF",
            "reporte.pdf",
            "PDF (*.pdf)",
        )

        if not ruta:
            return

        try:
            exportar_ventas_pdf(
                ventas,
                ruta,
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                str(e),
            )
            return

        QMessageBox.information(
            self,
            "Listo",
            f"Se exportó correctamente a:\n{ruta}",
        )