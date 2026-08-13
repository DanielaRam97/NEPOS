from datetime import date, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from services.cierre_service import listar_turnos_cerrados, calcular_resumen
from services.exportar_service import exportar_cierre_turno_excel, exportar_cierre_turno_pdf
from utils.formato import formatear_moneda, formatear_cantidad

OPCIONES_PERIODO = ["Todo el historial", "Hoy", "Esta semana", "Este mes"]


class VentanaReportesCierres(QWidget):
    def __init__(self):
        super().__init__()
        self.turnos_cargados = []
        self.resumen_seleccionado = None

        self.setWindowTitle("Reportes de cierres de caja")
        self.resize(900, 650)

        self._armar_interfaz()
        self.buscar()

    def _armar_interfaz(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3>Reportes de cierres de caja</h3>"))

        fila_periodo = QHBoxLayout()
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(OPCIONES_PERIODO)
        self.combo_periodo.currentTextChanged.connect(self.buscar)
        fila_periodo.addWidget(QLabel("Período:"))
        fila_periodo.addWidget(self.combo_periodo)
        fila_periodo.addStretch()
        layout.addLayout(fila_periodo)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            [
                "Fecha cierre", "Turno", "Cajero", "Venta bruta",
                "IVA 10,5%", "IVA 21%", "Efectivo", "Transacciones",
            ]
        )
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.itemSelectionChanged.connect(self._mostrar_detalle)
        layout.addWidget(self.tabla)

        self.etiqueta_totales_periodo = QLabel()
        self.etiqueta_totales_periodo.setWordWrap(True)
        self.etiqueta_totales_periodo.setStyleSheet(
            "font-weight: 800; color: #334155; padding: 6px;"
        )
        layout.addWidget(self.etiqueta_totales_periodo)

        self.etiqueta_detalle = QLabel("Seleccioná un cierre para ver el detalle.")
        self.etiqueta_detalle.setWordWrap(True)
        layout.addWidget(self.etiqueta_detalle)

        fila_acciones = QHBoxLayout()
        boton_excel = QPushButton("Exportar seleccionado a Excel")
        boton_excel.clicked.connect(self.exportar_excel)
        boton_pdf = QPushButton("Exportar seleccionado a PDF")
        boton_pdf.clicked.connect(self.exportar_pdf)
        fila_acciones.addWidget(boton_excel)
        fila_acciones.addWidget(boton_pdf)
        fila_acciones.addStretch()
        layout.addLayout(fila_acciones)

        self.setLayout(layout)

    def _rango_fechas(self):
        periodo = self.combo_periodo.currentText()
        hoy = date.today()
        if periodo == "Hoy":
            return hoy.isoformat(), hoy.isoformat()
        if periodo == "Esta semana":
            return (hoy - timedelta(days=hoy.weekday())).isoformat(), hoy.isoformat()
        if periodo == "Este mes":
            return hoy.replace(day=1).isoformat(), hoy.isoformat()
        return None, None

    def buscar(self):
        desde, hasta = self._rango_fechas()
        self.turnos_cargados = listar_turnos_cerrados(fecha_desde=desde, fecha_hasta=hasta)

        self.tabla.setRowCount(len(self.turnos_cargados))
        total_iva_10_5 = 0.0
        total_iva_21 = 0.0
        for fila, turno in enumerate(self.turnos_cargados):
            resumen = calcular_resumen(turno.id)
            total_iva_10_5 += resumen["iva_10_5"]
            total_iva_21 += resumen["iva_21"]
            cajero = turno.usuario.nombre if turno.usuario else "-"
            fecha_texto = turno.fecha_cierre.strftime("%d/%m/%Y %H:%M") if turno.fecha_cierre else "-"

            self.tabla.setItem(fila, 0, QTableWidgetItem(fecha_texto))
            self.tabla.setItem(fila, 1, QTableWidgetItem(turno.turno))
            self.tabla.setItem(fila, 2, QTableWidgetItem(cajero))
            self.tabla.setItem(fila, 3, QTableWidgetItem(formatear_moneda(resumen["venta_bruta"])))
            self.tabla.setItem(fila, 4, QTableWidgetItem(formatear_moneda(resumen["iva_10_5"])))
            self.tabla.setItem(fila, 5, QTableWidgetItem(formatear_moneda(resumen["iva_21"])))
            self.tabla.setItem(fila, 6, QTableWidgetItem(formatear_moneda(resumen["efectivo"])))
            self.tabla.setItem(fila, 7, QTableWidgetItem(str(resumen["transacciones"])))

        self.etiqueta_totales_periodo.setText(
            f"IVA acumulado del período — 10,5%: "
            f"{formatear_moneda(total_iva_10_5)}  |  21%: "
            f"{formatear_moneda(total_iva_21)}"
        )

        self.etiqueta_detalle.setText("Seleccioná un cierre para ver el detalle.")
        self.resumen_seleccionado = None

    def _mostrar_detalle(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return
        turno = self.turnos_cargados[filas[0].row()]
        resumen = calcular_resumen(turno.id)
        self.resumen_seleccionado = resumen

        self.etiqueta_detalle.setText(
            f"<b>Turno:</b> {resumen['turno']} — <b>Cajero:</b> {resumen['cajero']}<br>"
            f"Unidades vendidas: {formatear_cantidad(resumen['unidades'])} | "
            f"Pesables (kg): {formatear_cantidad(resumen['pesables'])}<br>"
            f"Recargos: {formatear_moneda(resumen['recargos'])} | "
            f"IVA 10,5%: {formatear_moneda(resumen['iva_10_5'])} | "
            f"IVA 21%: {formatear_moneda(resumen['iva_21'])}<br>"
            f"Efectivo: {formatear_moneda(resumen['efectivo'])} | "
            f"QR: {formatear_moneda(resumen['qr'])} | "
            f"Débito: {formatear_moneda(resumen['debito'])} | "
            f"Crédito: {formatear_moneda(resumen['credito'])}<br>"
            f"Fondo inicial: {formatear_moneda(resumen['fondo_inicial'])} | "
            f"Efectivo esperado: {formatear_moneda(resumen['efectivo_esperado_en_caja'])}<br>"
            f"Efectivo contado: "
            f"{formatear_moneda(resumen['efectivo_declarado']) if resumen.get('efectivo_declarado') is not None else '—'} | "
            f"Diferencia: "
            f"{formatear_moneda(resumen['diferencia_caja']) if resumen.get('diferencia_caja') is not None else '—'}<br>"
            f"Observación: {resumen.get('observacion_cierre') or '—'}"
        )

    def exportar_excel(self):
        if not self.resumen_seleccionado:
            QMessageBox.information(self, "Elegí un cierre", "Seleccioná un cierre de la tabla primero.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Excel", "cierre.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        try:
            exportar_cierre_turno_excel(self.resumen_seleccionado, ruta)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(self, "Listo", f"Se exportó correctamente a:\n{ruta}")

    def exportar_pdf(self):
        if not self.resumen_seleccionado:
            QMessageBox.information(self, "Elegí un cierre", "Seleccioná un cierre de la tabla primero.")
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "cierre.pdf", "PDF (*.pdf)")
        if not ruta:
            return
        try:
            exportar_cierre_turno_pdf(self.resumen_seleccionado, ruta)
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(self, "Listo", f"Se exportó correctamente a:\n{ruta}")
