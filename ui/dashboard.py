#from datetime import date, timedelta
#from PySide6.QtWidgets import (
#    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
#    QTableWidget, QTableWidgetItem, QHeaderView
#)
#from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
#from matplotlib.figure import Figure
#
#from services.reportes_service import resumen_periodo, ranking_productos, productos_stock_critico
#from utils.formato import formatear_moneda, formatear_cantidad
#
#OPCIONES_PERIODO = ["Hoy", "Esta semana", "Este mes", "Este año", "Todo el historial"]
#
#
#class VentanaDashboard(QWidget):
#    def __init__(self):
#        super().__init__()
#        self.setWindowTitle("NEPOS — Dashboard")
#        self.resize(1100, 760)
#
#        self._armar_interfaz()
#        self._actualizar()
#
#    def _armar_interfaz(self):
#        layout = QVBoxLayout()
#        titulo = QLabel("▥  DASHBOARD")
#        titulo.setObjectName("titulo_modulo")
#        layout.addWidget(titulo)
#        subtitulo = QLabel(
#            "Ventas, rentabilidad estimada y alertas de inventario."
#        )
#        subtitulo.setObjectName("subtitulo")
#        layout.addWidget(subtitulo)
#
#        fila_periodo = QHBoxLayout()
#        self.combo_periodo = QComboBox()
#        self.combo_periodo.addItems(OPCIONES_PERIODO)
#        self.combo_periodo.currentTextChanged.connect(self._actualizar)
#        fila_periodo.addWidget(QLabel("Período:"))
#        fila_periodo.addWidget(self.combo_periodo)
#        fila_periodo.addStretch()
#        layout.addLayout(fila_periodo)
#
#        fila_kpis = QHBoxLayout()
#        self.etiqueta_venta_bruta = self._crear_kpi("Ventas")
#        self.etiqueta_ganancia = self._crear_kpi("Ganancia estimada")
#        self.etiqueta_transacciones = self._crear_kpi("Transacciones")
#        self.etiqueta_unidades = self._crear_kpi("Unidades vendidas")
#        for etiqueta in (self.etiqueta_venta_bruta, self.etiqueta_ganancia,
#                         self.etiqueta_transacciones, self.etiqueta_unidades):
#            fila_kpis.addWidget(etiqueta)
#        layout.addLayout(fila_kpis)
#
#        fila_contenido = QHBoxLayout()
#
#        columna_izquierda = QVBoxLayout()
#        columna_izquierda.addWidget(QLabel("<b>Ranking de productos (por facturación)</b>"))
#        self.figura = Figure(figsize=(5, 4))
#        self.canvas = FigureCanvasQTAgg(self.figura)
#        columna_izquierda.addWidget(self.canvas)
#        fila_contenido.addLayout(columna_izquierda, stretch=2)
#
#        columna_derecha = QVBoxLayout()
#        columna_derecha.addWidget(QLabel("<b>Stock crítico (5 unidades o menos)</b>"))
#        self.tabla_stock_critico = QTableWidget(0, 3)
#        self.tabla_stock_critico.setAlternatingRowColors(True)
#        self.tabla_stock_critico.setHorizontalHeaderLabels(["Código", "Producto", "Stock"])
#        self.tabla_stock_critico.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
#        columna_derecha.addWidget(self.tabla_stock_critico)
#        fila_contenido.addLayout(columna_derecha, stretch=1)
#
#        layout.addLayout(fila_contenido)
#        self.setLayout(layout)
#
#    def _crear_kpi(self, titulo):
#        etiqueta = QLabel(f"<div style='text-align:center;'><small>{titulo}</small><br>"
#                           f"<span style='font-size:20px; font-weight:bold;'>—</span></div>")
#        etiqueta.setStyleSheet(
#            "background:#ffffff; border:1px solid #cbd5e1;"
#            "border-radius:10px; padding:14px; color:#172033;"
#        )
#        etiqueta.titulo = titulo
#        return etiqueta
#
#    def _setear_kpi(self, etiqueta, valor):
#        etiqueta.setText(
#            f"<div style='text-align:center;'><small>{etiqueta.titulo}</small><br>"
#            f"<span style='font-size:20px; font-weight:bold;'>{valor}</span></div>"
#        )
#
#    def _rango_fechas(self):
#        periodo = self.combo_periodo.currentText()
#        hoy = date.today()
#
#        if periodo == "Hoy":
#            desde = hoy
#        elif periodo == "Esta semana":
#            desde = hoy - timedelta(days=hoy.weekday())
#        elif periodo == "Este mes":
#            desde = hoy.replace(day=1)
#        elif periodo == "Este año":
#            desde = hoy.replace(month=1, day=1)
#        else:
#            return None, None  # "Todo el historial"
#
#        return desde.isoformat(), hoy.isoformat()
#
#    def _actualizar(self):
#        fecha_desde, fecha_hasta = self._rango_fechas()
#
#        resumen = resumen_periodo(fecha_desde, fecha_hasta)
#        self._setear_kpi(self.etiqueta_venta_bruta, formatear_moneda(resumen["venta_bruta"]))
#        self._setear_kpi(self.etiqueta_ganancia, formatear_moneda(resumen["ganancia_estimada"]))
#        self._setear_kpi(self.etiqueta_transacciones, str(resumen["transacciones"]))
#        self._setear_kpi(self.etiqueta_unidades, formatear_cantidad(resumen["unidades"]))
#
#        ranking = ranking_productos(fecha_desde, fecha_hasta)
#        self._dibujar_ranking(ranking)
#
#        stock_critico = productos_stock_critico()
#        self.tabla_stock_critico.setRowCount(len(stock_critico))
#        for fila, producto in enumerate(stock_critico):
#            self.tabla_stock_critico.setItem(fila, 0, QTableWidgetItem(producto.codigo))
#            self.tabla_stock_critico.setItem(fila, 1, QTableWidgetItem(producto.descripcion))
#            self.tabla_stock_critico.setItem(fila, 2, QTableWidgetItem(formatear_cantidad(producto.stock)))
#
#    def _dibujar_ranking(self, ranking):
#        self.figura.clear()
#        ax = self.figura.subplots()
#
#        if not ranking:
#            ax.text(0.5, 0.5, "Sin ventas en este período", ha="center", va="center")
#            self.canvas.draw()
#            return
#
#        ranking_invertido = list(reversed(ranking))  # para que el más vendido quede arriba
#        nombres = [r["descripcion"] for r in ranking_invertido]
#        totales = [r["total"] for r in ranking_invertido]
#
#        self.figura.patch.set_facecolor("#ffffff")
#        ax.set_facecolor("#ffffff")
#        ax.barh(nombres, totales, color="#12aa52")
#        ax.set_xlabel("Facturación ($)")
#        ax.spines["top"].set_visible(False)
#        ax.spines["right"].set_visible(False)
#        self.figura.tight_layout()
#        self.canvas.draw()
#