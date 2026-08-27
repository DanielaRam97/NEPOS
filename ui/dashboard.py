from datetime import date, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.reportes_service import (
    productos_stock_critico,
    ranking_productos,
    resumen_periodo,
)
from ui.estilos import ESTILO_GLOBAL
from utils.formato import formatear_cantidad, formatear_moneda


OPCIONES_PERIODO = [
    "Hoy",
    "Esta semana",
    "Este mes",
    "Este año",
    "Todo el historial",
]


class VentanaDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("NEPOS — Dashboard")
        self.resize(1180, 760)
        self.setMinimumSize(950, 650)
        self.setStyleSheet(ESTILO_GLOBAL)

        self._armar_interfaz()
        self._actualizar()

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)

        cabecera = QFrame()
        cabecera.setObjectName("tarjeta")
        fila_cabecera = QHBoxLayout(cabecera)

        textos = QVBoxLayout()
        titulo = QLabel("DASHBOARD ADMINISTRATIVO")
        titulo.setObjectName("titulo_modulo")
        subtitulo = QLabel(
            "Ventas confirmadas, productos destacados y alertas de stock."
        )
        subtitulo.setObjectName("subtitulo")

        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(OPCIONES_PERIODO)
        self.combo_periodo.currentTextChanged.connect(
            self._actualizar
        )

        boton_actualizar = QPushButton("Actualizar")
        boton_actualizar.clicked.connect(self._actualizar)

        fila_cabecera.addLayout(textos)
        fila_cabecera.addStretch()
        fila_cabecera.addWidget(QLabel("Período:"))
        fila_cabecera.addWidget(self.combo_periodo)
        fila_cabecera.addWidget(boton_actualizar)

        layout.addWidget(cabecera)

        grilla_kpis = QGridLayout()
        grilla_kpis.setHorizontalSpacing(10)
        grilla_kpis.setVerticalSpacing(10)

        self.kpi_ventas = self._crear_kpi("Ventas brutas")
        self.kpi_transacciones = self._crear_kpi("Transacciones")
        self.kpi_ticket = self._crear_kpi("Ticket promedio")
        self.kpi_unidades = self._crear_kpi("Unidades vendidas")
        self.kpi_margen = self._crear_kpi("Margen bruto")

        grilla_kpis.addWidget(self.kpi_ventas, 0, 0)
        grilla_kpis.addWidget(self.kpi_transacciones, 0, 1)
        grilla_kpis.addWidget(self.kpi_ticket, 0, 2)
        grilla_kpis.addWidget(self.kpi_unidades, 0, 3)
        grilla_kpis.addWidget(self.kpi_margen, 0, 4)

        layout.addLayout(grilla_kpis)

        contenido = QHBoxLayout()
        contenido.setSpacing(10)

        bloque_ranking = QFrame()
        bloque_ranking.setObjectName("tarjeta")
        ranking_layout = QVBoxLayout(bloque_ranking)

        ranking_layout.addWidget(
            QLabel("<b>Productos más vendidos por facturación</b>")
        )

        self.tabla_ranking = QTableWidget(0, 3)
        self.tabla_ranking.setHorizontalHeaderLabels(
            ["Producto", "Cantidad", "Facturación"]
        )
        self.tabla_ranking.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_ranking.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_ranking.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.Stretch,
        )
        ranking_layout.addWidget(self.tabla_ranking)

        contenido.addWidget(bloque_ranking, 2)

        bloque_stock = QFrame()
        bloque_stock.setObjectName("tarjeta")
        stock_layout = QVBoxLayout(bloque_stock)

        stock_layout.addWidget(
            QLabel("<b>Alertas de stock crítico</b>")
        )

        self.tabla_stock = QTableWidget(0, 3)
        self.tabla_stock.setHorizontalHeaderLabels(
            ["Código", "Producto", "Stock"]
        )
        self.tabla_stock.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_stock.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_stock.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        stock_layout.addWidget(self.tabla_stock)

        contenido.addWidget(bloque_stock, 1)

        layout.addLayout(contenido, 1)

        self.etiqueta_aviso = QLabel()
        self.etiqueta_aviso.setWordWrap(True)
        self.etiqueta_aviso.setStyleSheet(
            "color: #92400e; background: #fffbeb; "
            "border: 1px solid #fcd34d; border-radius: 7px; "
            "padding: 8px; font-weight: 600;"
        )
        layout.addWidget(self.etiqueta_aviso)

    def _crear_kpi(self, titulo):
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)

        etiqueta_titulo = QLabel(titulo.upper())
        etiqueta_titulo.setStyleSheet(
            "color: #64748b; font-size: 11px; font-weight: 800;"
        )

        etiqueta_valor = QLabel("—")
        etiqueta_valor.setStyleSheet(
            "color: #172033; font-size: 24px; font-weight: 900;"
        )
        etiqueta_valor.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addWidget(etiqueta_titulo)
        layout.addWidget(etiqueta_valor)

        tarjeta.etiqueta_valor = etiqueta_valor
        return tarjeta

    @staticmethod
    def _setear_kpi(tarjeta, valor):
        tarjeta.etiqueta_valor.setText(valor)

    def _rango_fechas(self):
        hoy = date.today()
        periodo = self.combo_periodo.currentText()

        if periodo == "Hoy":
            desde = hoy
        elif periodo == "Esta semana":
            desde = hoy - timedelta(days=hoy.weekday())
        elif periodo == "Este mes":
            desde = hoy.replace(day=1)
        elif periodo == "Este año":
            desde = hoy.replace(month=1, day=1)
        else:
            return None, None

        return desde.isoformat(), hoy.isoformat()

    def _actualizar(self):
        fecha_desde, fecha_hasta = self._rango_fechas()

        resumen = resumen_periodo(
            fecha_desde,
            fecha_hasta,
        )
        ranking = ranking_productos(
            fecha_desde,
            fecha_hasta,
        )
        stock_critico = productos_stock_critico()

        self._setear_kpi(
            self.kpi_ventas,
            formatear_moneda(resumen["venta_bruta"]),
        )
        self._setear_kpi(
            self.kpi_transacciones,
            str(resumen["transacciones"]),
        )
        self._setear_kpi(
            self.kpi_ticket,
            formatear_moneda(resumen["ticket_promedio"]),
        )
        self._setear_kpi(
            self.kpi_unidades,
            formatear_cantidad(resumen["unidades"]),
        )

        if resumen["rentabilidad_completa"]:
            self._setear_kpi(
                self.kpi_margen,
                formatear_moneda(resumen["ganancia_estimada"]),
            )
            self.etiqueta_aviso.setText(
                "Margen bruto calculado con el costo histórico "
                "guardado en cada venta."
            )
            self.etiqueta_aviso.setStyleSheet(
                "color: #166534; background: #f0fdf4; "
                "border: 1px solid #86efac; border-radius: 7px; "
                "padding: 8px; font-weight: 600;"
            )
        else:
            self._setear_kpi(
                self.kpi_margen,
                "Datos incompletos",
            )
            self.etiqueta_aviso.setText(
                "El margen no se muestra porque este período contiene "
                f"{resumen['lineas_sin_costo_historico']} líneas de ventas "
                "anteriores sin costo histórico."
            )
            self.etiqueta_aviso.setStyleSheet(
                "color: #92400e; background: #fffbeb; "
                "border: 1px solid #fcd34d; border-radius: 7px; "
                "padding: 8px; font-weight: 600;"
            )

        self.tabla_ranking.setRowCount(len(ranking))
        for fila, producto in enumerate(ranking):
            self.tabla_ranking.setItem(
                fila,
                0,
                QTableWidgetItem(producto["descripcion"]),
            )
            self.tabla_ranking.setItem(
                fila,
                1,
                QTableWidgetItem(
                    formatear_cantidad(producto["unidades"])
                ),
            )
            self.tabla_ranking.setItem(
                fila,
                2,
                QTableWidgetItem(
                    formatear_moneda(producto["total"])
                ),
            )

        self.tabla_stock.setRowCount(len(stock_critico))
        for fila, producto in enumerate(stock_critico):
            self.tabla_stock.setItem(
                fila,
                0,
                QTableWidgetItem(producto.codigo),
            )
            self.tabla_stock.setItem(
                fila,
                1,
                QTableWidgetItem(producto.descripcion),
            )
            self.tabla_stock.setItem(
                fila,
                2,
                QTableWidgetItem(
                    formatear_cantidad(producto.stock)
                ),
            )