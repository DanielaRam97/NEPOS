from datetime import date, timedelta
from utils.rutas import ruta_icono

from PySide6.QtCore import QDate, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.historial_service import (
    listar_cajeros,
    listar_ventas,
)
from services.impresion_service import (
    ErrorImpresion,
    imprimir_ticket_historico,
)
from services.venta_service import (
    ErrorVenta,
    anular_venta,
)
from ui.estilos import ESTILO_GLOBAL
from utils.formato import (
    formatear_cantidad,
    formatear_moneda,
)


OPCIONES_PERIODO = [
    "Todo el historial",
    "Hoy",
    "Esta semana",
    "Este mes",
    "Este año",
    "Personalizado",
]

ROL_ORDEN = int(Qt.ItemDataRole.UserRole)
ROL_VENTA_ID = ROL_ORDEN + 1


class ItemOrdenable(QTableWidgetItem):
    """Permite ordenar fechas y números por su valor real."""

    def __init__(self, texto, valor_orden=None):
        super().__init__(str(texto))
        self.setData(
            ROL_ORDEN,
            valor_orden if valor_orden is not None else str(texto),
        )

    def __lt__(self, otro):
        valor_propio = self.data(ROL_ORDEN)
        valor_otro = otro.data(ROL_ORDEN)

        try:
            return valor_propio < valor_otro
        except TypeError:
            return str(valor_propio).casefold() < str(
                valor_otro
            ).casefold()


class VentanaHistorial(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.ventas_cargadas = []
        self.ventas_por_id = {}
        self.boton_anular = None

        self.setWindowTitle("NEPOS — Historial de ventas")
        self.resize(1100, 760)
        self.setMinimumSize(940, 680)
        self.setStyleSheet(ESTILO_GLOBAL)

        self._armar_interfaz()
        self._cargar_cajeros()
        self._cambio_periodo()

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)

        # =====================================================
        # CABECERA
        # =====================================================
        cabecera = QFrame()
        cabecera.setObjectName("tarjeta")

        fila_cabecera = QHBoxLayout(cabecera)
        fila_cabecera.setContentsMargins(18, 10, 18, 10)
        fila_cabecera.setSpacing(11)

        icono = QLabel()
        pixmap = QPixmap(str(ruta_icono("historial_ventas.png")))

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
            icono.setText("▤")
            icono.setStyleSheet(
                "font-size:26px; font-weight:900; color:#4da8da;"
            )

        icono.setFixedSize(40, 40)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setContentsMargins(0, 0, 0, 0)
        bloque_titulo.setSpacing(1)

        titulo = QLabel("HISTORIAL DE VENTAS")
        titulo.setObjectName("titulo_modulo")

        ayuda = QLabel(
            "Consultá ventas, medios de pago y productos vendidos."
        )
        ayuda.setObjectName("subtitulo")

        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(ayuda)

        fila_cabecera.addWidget(icono)
        fila_cabecera.addLayout(bloque_titulo)
        fila_cabecera.addStretch()

        layout.addWidget(cabecera)

        # =====================================================
        # FILTROS
        # =====================================================
        filtros_frame = QFrame()
        filtros_frame.setObjectName("tarjeta")

        filtros = QGridLayout(filtros_frame)
        filtros.setContentsMargins(14, 10, 14, 10)
        filtros.setHorizontalSpacing(9)
        filtros.setVerticalSpacing(5)

        filtros.addWidget(QLabel("Período"), 0, 0)
        filtros.addWidget(QLabel("Desde"), 0, 1)
        filtros.addWidget(QLabel("Hasta"), 0, 2)
        filtros.addWidget(QLabel("Cajero"), 0, 3)

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(OPCIONES_PERIODO)
        self.combo_periodo.setMinimumHeight(42)

        hoy = QDate.currentDate()

        self.campo_desde = QDateEdit()
        self.campo_desde.setDate(hoy)
        self.campo_desde.setDisplayFormat("dd/MM/yyyy")
        self.campo_desde.setCalendarPopup(True)
        self.campo_desde.setMinimumHeight(42)

        self.campo_hasta = QDateEdit()
        self.campo_hasta.setDate(hoy)
        self.campo_hasta.setDisplayFormat("dd/MM/yyyy")
        self.campo_hasta.setCalendarPopup(True)
        self.campo_hasta.setMinimumHeight(42)

        self.combo_cajero = QComboBox()
        self.combo_cajero.addItem(
            "Todos los cajeros",
            None,
        )
        self.combo_cajero.setMinimumHeight(42)

        boton_buscar = QPushButton("🔍  BUSCAR")
        boton_buscar.setObjectName("buscar_historial")
        boton_buscar.setMinimumHeight(42)
        boton_buscar.clicked.connect(self.buscar)

        boton_limpiar = QPushButton("LIMPIAR")
        boton_limpiar.setObjectName("limpiar_historial")
        boton_limpiar.setMinimumHeight(42)
        boton_limpiar.clicked.connect(
            self.limpiar_filtros
        )

        filtros.addWidget(self.combo_periodo, 1, 0)
        filtros.addWidget(self.campo_desde, 1, 1)
        filtros.addWidget(self.campo_hasta, 1, 2)
        filtros.addWidget(self.combo_cajero, 1, 3)
        filtros.addWidget(boton_buscar, 1, 4)
        filtros.addWidget(boton_limpiar, 1, 5)

        filtros.setColumnStretch(0, 2)
        filtros.setColumnStretch(1, 1)
        filtros.setColumnStretch(2, 1)
        filtros.setColumnStretch(3, 2)
        filtros.setColumnStretch(4, 0)
        filtros.setColumnStretch(5, 0)

        self.combo_periodo.currentTextChanged.connect(
            self._cambio_periodo
        )
        self.combo_cajero.currentIndexChanged.connect(
            self.buscar
        )

        layout.addWidget(filtros_frame)

        # =====================================================
        # DIVISOR ENTRE VENTAS Y DETALLE
        # =====================================================
        self.divisor = QSplitter(
            Qt.Orientation.Vertical
        )
        self.divisor.setChildrenCollapsible(False)

        # =====================================================
        # TABLA DE VENTAS
        # =====================================================
        ventas_frame = QFrame()
        ventas_frame.setObjectName("tarjeta")

        ventas_layout = QVBoxLayout(ventas_frame)
        ventas_layout.setContentsMargins(7, 7, 7, 7)
        ventas_layout.setSpacing(5)

        titulo_ventas = QLabel("VENTAS REGISTRADAS")
        titulo_ventas.setObjectName("titulo_tabla_historial")
        ventas_layout.addWidget(titulo_ventas)

        self.tabla_ventas = QTableWidget(0, 7)
        self.tabla_ventas.setAlternatingRowColors(True)
        self.tabla_ventas.setHorizontalHeaderLabels(
            [
                "N.º",
                "FECHA",
                "CAJERO",
                "TURNO",
                "FORMA DE PAGO",
                "TOTAL",
                "ESTADO",
            ]
        )
        self.tabla_ventas.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_ventas.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabla_ventas.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_ventas.verticalHeader().setVisible(False)
        self.tabla_ventas.verticalHeader().setDefaultSectionSize(
            35
        )

        header_ventas = self.tabla_ventas.horizontalHeader()
        header_ventas.setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        header_ventas.setSectionsClickable(True)
        header_ventas.setSortIndicatorShown(True)

        self.tabla_ventas.setSortingEnabled(True)
        self.tabla_ventas.itemSelectionChanged.connect(
            self._mostrar_detalle
        )
        self.tabla_ventas.cellClicked.connect(
            self._seleccionar_fila
        )

        ventas_layout.addWidget(self.tabla_ventas)
        self.divisor.addWidget(ventas_frame)

        # =====================================================
        # DETALLE DE LA VENTA
        # =====================================================
        detalle_frame = QFrame()
        detalle_frame.setObjectName("tarjeta")

        detalle_layout = QVBoxLayout(detalle_frame)
        detalle_layout.setContentsMargins(7, 7, 7, 7)
        detalle_layout.setSpacing(6)

        cabecera_detalle = QHBoxLayout()

        self.etiqueta_detalle = QLabel(
            "Seleccioná una venta para consultar su detalle."
        )
        self.etiqueta_detalle.setObjectName(
            "titulo_detalle_historial"
        )
        cabecera_detalle.addWidget(self.etiqueta_detalle)
        cabecera_detalle.addStretch()

        self.boton_reimprimir = QPushButton(
            "REIMPRIMIR TICKET"
        )
        self.boton_reimprimir.setObjectName(
            "reimprimir_ticket"
        )
        self.boton_reimprimir.setEnabled(False)
        self.boton_reimprimir.setMinimumHeight(40)

        icono_reimprimir = self.style().standardIcon(
            QStyle.StandardPixmap.SP_BrowserReload
        )
        self.boton_reimprimir.setIcon(icono_reimprimir)
        self.boton_reimprimir.setIconSize(QSize(20, 20))
        self.boton_reimprimir.clicked.connect(
            self.reimprimir_ticket
        )

        cabecera_detalle.addWidget(
            self.boton_reimprimir
        )

        if self.usuario.rol in ("SUPERVISOR", "ADMIN"):
            self.boton_anular = QPushButton(
                "ANULAR VENTA"
            )
            self.boton_anular.setObjectName(
                "anular_venta_historial"
            )
            self.boton_anular.setEnabled(False)
            self.boton_anular.setMinimumHeight(40)

            icono_anular = self.style().standardIcon(
                QStyle.StandardPixmap.SP_DialogCancelButton
            )
            self.boton_anular.setIcon(icono_anular)
            self.boton_anular.setIconSize(QSize(20, 20))
            self.boton_anular.clicked.connect(self.anular)

            cabecera_detalle.addWidget(
                self.boton_anular
            )

        detalle_layout.addLayout(cabecera_detalle)

        self.tabla_detalle = QTableWidget(0, 4)
        self.tabla_detalle.setAlternatingRowColors(True)
        self.tabla_detalle.setHorizontalHeaderLabels(
            [
                "PRODUCTO",
                "CANTIDAD",
                "PRECIO",
                "SUBTOTAL",
            ]
        )
        self.tabla_detalle.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_detalle.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.verticalHeader().setDefaultSectionSize(
            34
        )

        header_detalle = self.tabla_detalle.horizontalHeader()
        header_detalle.setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        header_detalle.setSectionsClickable(True)
        header_detalle.setSortIndicatorShown(True)

        self.tabla_detalle.setSortingEnabled(True)

        detalle_layout.addWidget(self.tabla_detalle)
        self.divisor.addWidget(detalle_frame)

        self.divisor.setStretchFactor(0, 3)
        self.divisor.setStretchFactor(1, 2)
        self.divisor.setSizes([350, 250])

        layout.addWidget(self.divisor, 1)

        QTimer.singleShot(
            0,
            self._ajustar_columnas,
        )

    def _cargar_cajeros(self):
        self.combo_cajero.blockSignals(True)

        for cajero in listar_cajeros():
            self.combo_cajero.addItem(
                cajero.nombre,
                cajero.id,
            )

        self.combo_cajero.blockSignals(False)

    def _cambio_periodo(self, _valor=None):
        periodo = self.combo_periodo.currentText()
        hoy = date.today()

        if periodo == "Hoy":
            desde = hoy
        elif periodo == "Esta semana":
            desde = hoy - timedelta(
                days=hoy.weekday()
            )
        elif periodo == "Este mes":
            desde = hoy.replace(day=1)
        elif periodo == "Este año":
            desde = hoy.replace(
                month=1,
                day=1,
            )
        else:
            desde = hoy

        personalizado = periodo == "Personalizado"

        self.campo_desde.setEnabled(personalizado)
        self.campo_hasta.setEnabled(personalizado)

        if not personalizado:
            self.campo_desde.setDate(
                QDate(
                    desde.year,
                    desde.month,
                    desde.day,
                )
            )
            self.campo_hasta.setDate(
                QDate(
                    hoy.year,
                    hoy.month,
                    hoy.day,
                )
            )
            self.buscar()

    def limpiar_filtros(self):
        self.combo_periodo.blockSignals(True)
        self.combo_cajero.blockSignals(True)

        self.combo_periodo.setCurrentIndex(0)
        self.combo_cajero.setCurrentIndex(0)

        self.combo_periodo.blockSignals(False)
        self.combo_cajero.blockSignals(False)

        self._cambio_periodo()

    def buscar(self, _valor=None):
        if (
            self.combo_periodo.currentText()
            == "Todo el historial"
        ):
            fecha_desde = None
            fecha_hasta = None
        else:
            fecha_desde = (
                self.campo_desde.date().toPython()
            )
            fecha_hasta = (
                self.campo_hasta.date().toPython()
            )

            if fecha_desde > fecha_hasta:
                QMessageBox.warning(
                    self,
                    "Período inválido",
                    "La fecha Desde no puede ser posterior "
                    "a la fecha Hasta.",
                )
                return

        try:
            self.ventas_cargadas = listar_ventas(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                usuario_id=self.combo_cajero.currentData(),
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                "No se pudo consultar",
                str(error),
            )
            return

        self.ventas_por_id = {
            venta.id: venta
            for venta in self.ventas_cargadas
        }

        self.tabla_ventas.setSortingEnabled(False)
        self.tabla_ventas.setRowCount(
            len(self.ventas_cargadas)
        )

        for fila, venta in enumerate(
            self.ventas_cargadas
        ):
            numero = venta.numero or venta.id
            cajero = (
                venta.usuario.nombre
                if venta.usuario
                else "-"
            )
            turno = (
                venta.turno_rel.turno
                if venta.turno_rel
                else "-"
            )
            forma_pago = venta.forma_pago or "-"
            total = float(venta.total or 0)
            anulada = bool(venta.anulada)
            estado = "Anulada" if anulada else "Activa"

            items = [
                ItemOrdenable(
                    numero,
                    float(numero),
                ),
                ItemOrdenable(
                    venta.fecha.strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    venta.fecha.timestamp(),
                ),
                ItemOrdenable(
                    cajero,
                    cajero.casefold(),
                ),
                ItemOrdenable(
                    turno,
                    turno.casefold(),
                ),
                ItemOrdenable(
                    forma_pago,
                    forma_pago.casefold(),
                ),
                ItemOrdenable(
                    formatear_moneda(total),
                    total,
                ),
                ItemOrdenable(
                    estado,
                    1 if anulada else 0,
                ),
            ]

            for columna, item in enumerate(items):
                item.setData(
                    ROL_VENTA_ID,
                    venta.id,
                )

                if columna in (0, 5, 6):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                if anulada:
                    item.setForeground(
                        QColor("#b91c1c")
                    )

                self.tabla_ventas.setItem(
                    fila,
                    columna,
                    item,
                )

        self.tabla_ventas.setSortingEnabled(True)
        self.tabla_ventas.sortItems(
            1,
            Qt.SortOrder.DescendingOrder,
        )

        self._limpiar_detalle()
        QTimer.singleShot(
            0,
            self._ajustar_columnas,
        )

    def _seleccionar_fila(self, fila, _columna):
        if 0 <= fila < self.tabla_ventas.rowCount():
            self.tabla_ventas.selectRow(fila)

    def _venta_seleccionada(self):
        filas = (
            self.tabla_ventas
            .selectionModel()
            .selectedRows()
        )

        if not filas:
            return None

        fila = filas[0].row()
        item_numero = self.tabla_ventas.item(fila, 0)

        if item_numero is None:
            return None

        venta_id = item_numero.data(ROL_VENTA_ID)
        return self.ventas_por_id.get(venta_id)

    def _mostrar_detalle(self):
        venta = self._venta_seleccionada()

        if venta is None:
            self._limpiar_detalle()
            return

        numero = venta.numero or venta.id
        estado = "ANULADA" if venta.anulada else "ACTIVA"

        self.etiqueta_detalle.setText(
            f"VENTA N.º {numero} · "
            f"{venta.forma_pago or '-'} · "
            f"{formatear_moneda(venta.total)} · "
            f"{estado}"
        )

        self.boton_reimprimir.setEnabled(True)

        if self.boton_anular:
            self.boton_anular.setEnabled(
                not bool(venta.anulada)
            )

        self.tabla_detalle.setSortingEnabled(False)
        self.tabla_detalle.setRowCount(
            len(venta.items)
        )

        for fila, detalle in enumerate(venta.items):
            descripcion = (
                detalle.producto.descripcion
                if detalle.producto
                else "(producto eliminado)"
            )
            cantidad = float(detalle.cantidad or 0)
            precio = float(
                detalle.precio_unitario or 0
            )
            subtotal = float(detalle.subtotal or 0)

            valores = [
                ItemOrdenable(
                    descripcion,
                    descripcion.casefold(),
                ),
                ItemOrdenable(
                    formatear_cantidad(cantidad),
                    cantidad,
                ),
                ItemOrdenable(
                    formatear_moneda(precio),
                    precio,
                ),
                ItemOrdenable(
                    formatear_moneda(subtotal),
                    subtotal,
                ),
            ]

            for columna, item in enumerate(valores):
                if columna > 0:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.tabla_detalle.setItem(
                    fila,
                    columna,
                    item,
                )

        self.tabla_detalle.setSortingEnabled(True)

        QTimer.singleShot(
            0,
            self._ajustar_columnas,
        )

    def _limpiar_detalle(self):
        self.tabla_detalle.setRowCount(0)
        self.etiqueta_detalle.setText(
            "Seleccioná una venta para consultar su detalle."
        )
        self.boton_reimprimir.setEnabled(False)

        if self.boton_anular:
            self.boton_anular.setEnabled(False)

    def _ajustar_columnas(self):
        ancho_ventas = (
            self.tabla_ventas.viewport().width()
        )

        if ancho_ventas > 0:
            proporciones_ventas = (
                0.07,
                0.17,
                0.19,
                0.15,
                0.16,
                0.16,
                0.10,
            )
            anchos = [
                int(ancho_ventas * proporcion)
                for proporcion in proporciones_ventas
            ]
            anchos[-1] += ancho_ventas - sum(anchos)

            for columna, ancho in enumerate(anchos):
                self.tabla_ventas.setColumnWidth(
                    columna,
                    ancho,
                )

        ancho_detalle = (
            self.tabla_detalle.viewport().width()
        )

        if ancho_detalle > 0:
            proporciones_detalle = (
                0.58,
                0.12,
                0.15,
                0.15,
            )
            anchos = [
                int(ancho_detalle * proporcion)
                for proporcion in proporciones_detalle
            ]
            anchos[-1] += ancho_detalle - sum(anchos)

            for columna, ancho in enumerate(anchos):
                self.tabla_detalle.setColumnWidth(
                    columna,
                    ancho,
                )

    def resizeEvent(self, evento):
        super().resizeEvent(evento)

        QTimer.singleShot(
            0,
            self._ajustar_columnas,
        )

    def reimprimir_ticket(self):
        venta = self._venta_seleccionada()

        if venta is None:
            QMessageBox.information(
                self,
                "Elegí una venta",
                "Seleccioná una venta para reimprimir.",
            )
            return

        numero = venta.numero or venta.id

        respuesta = QMessageBox.question(
            self,
            "Reimprimir ticket",
            f"¿Querés reimprimir el ticket de la venta "
            f"N.º {numero}?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        try:
            imprimir_ticket_historico(venta)
        except ErrorImpresion as error:
            QMessageBox.warning(
                self,
                "No se pudo imprimir",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Ticket enviado",
            "El ticket fue enviado a la impresora configurada.",
        )

    def anular(self):
        if self.usuario.rol not in (
            "SUPERVISOR",
            "ADMIN",
        ):
            QMessageBox.warning(
                self,
                "Acción no permitida",
                "Solo SUPERVISOR o ADMIN pueden anular ventas.",
            )
            return

        venta = self._venta_seleccionada()

        if venta is None:
            QMessageBox.information(
                self,
                "Elegí una venta",
                "Seleccioná una venta primero.",
            )
            return

        if venta.anulada:
            QMessageBox.information(
                self,
                "Ya anulada",
                "Esta venta ya estaba anulada.",
            )
            return

        numero = venta.numero or venta.id

        motivo, aceptado = QInputDialog.getText(
            self,
            "Anular venta",
            f"Motivo de la anulación de la venta "
            f"N.º {numero}:",
        )

        if not aceptado or not motivo.strip():
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar anulación",
            f"¿Confirmás anular la venta N.º {numero}?\n\n"
            f"Total: {formatear_moneda(venta.total)}\n"
            "El stock de todos sus productos será repuesto.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        try:
            anular_venta(
                venta.id,
                motivo.strip(),
                self.usuario.id,
            )
        except ErrorVenta as error:
            QMessageBox.warning(
                self,
                "No se pudo anular",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Venta anulada",
            "La venta se anuló y el stock fue repuesto.",
        )

        self.buscar()