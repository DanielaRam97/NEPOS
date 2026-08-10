from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt

from services.configuracion_service import (
    obtener_configuracion_caja,
    obtener_configuracion_comercio,
)
from services.promocion_service import calcular_descuento_promociones
from utils.formato import formatear_moneda
from utils.validacion import convertir_decimal_finito


MEDIOS = {
    "EFECTIVO": "Efectivo",
    "QR": "Transferencia / QR",
    "DEBITO": "Tarjeta de débito",
    "CREDITO": "Tarjeta de crédito",
}
MEDIOS_ELECTRONICOS = {"QR", "DEBITO", "CREDITO"}


class DialogoPago(QDialog):
    def __init__(self, carrito, parent=None):
        super().__init__(parent)
        self.carrito = carrito
        self.resultado_pago = None
        self.subtotal = round(
            sum(float(item.get("subtotal", item.get("total", 0))) for item in carrito),
            2,
        )
        self.subtotal_cigarrillos = round(
            sum(
                float(item.get("subtotal", item.get("total", 0)))
                for item in carrito
                if (item.get("categoria") or "").upper() == "CIGARRILLOS"
            ),
            2,
        )
        try:
            (
                self.descuento_promociones,
                self.aplicaciones_promociones,
            ) = calcular_descuento_promociones(self.carrito)
        except Exception:
            # El servicio de venta vuelve a validar el descuento al confirmar.
            self.descuento_promociones = 0.0
            self.aplicaciones_promociones = []
        try:
            self.configuracion = obtener_configuracion_caja()
        except Exception:
            self.configuracion = {
                "recargo_cigarrillos": 0.15,
                "recargo_credito": 0.15,
                "medios_pago": list(MEDIOS),
            }

        habilitados = self.configuracion.get("medios_pago") or list(MEDIOS)
        self.medios_habilitados = [
            medio for medio in habilitados if medio in MEDIOS
        ]
        if not self.medios_habilitados:
            self.medios_habilitados = list(MEDIOS)

        self.setWindowTitle("Confirmar cobro")
        self.setModal(True)
        self.setMinimumSize(620, 440)
        self.setStyleSheet(
            """
            QDialog {
                background: #f4f6f8;
                color: #172033;
            }

            QLabel {
                background: transparent;
                color: #172033;
            }

            QLabel#titulo_pago {
                font-size: 25px;
                font-weight: 900;
                color: #101827;
                padding: 4px;
            }

            QLabel#etiqueta_formulario {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
            }

            QFrame#tarjeta_pago {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
            }

            QLineEdit, QComboBox {
                min-height: 25px;
                background: #ffffff;
                color: #172033;
                border: 1px solid #aeb8c6;
                border-radius: 7px;
                padding: 7px 10px;
            }

            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #12aa52;
            }

            QCheckBox {
                color: #172033;
                font-size: 13px;
                font-weight: 600;
                spacing: 9px;
                padding: 4px;
            }

            QCheckBox::indicator {
                width: 19px;
                height: 19px;
                background: #ffffff;
                border: 2px solid #7c8798;
                border-radius: 4px;
            }

            QCheckBox::indicator:hover {
                border: 2px solid #12aa52;
            }

            QCheckBox::indicator:checked {
                background: #12aa52;
                border: 2px solid #0d9245;
            }

            QCheckBox::indicator:disabled {
                background: #e5e7eb;
                border: 2px solid #c4cad2;
            }

            QPushButton {
                min-height: 24px;
                padding: 8px 18px;
                border: none;
                border-radius: 7px;
                background: #e5e7eb;
                color: #172033;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #d5d9df;
            }

            QPushButton#confirmar {
                background: #12aa52;
                color: #ffffff;
                font-weight: 800;
            }

            QPushButton#confirmar:hover {
                background: #0d9245;
            }
            """
        )
        self._armar_interfaz()
        self._actualizar_resumen()

    def _armar_interfaz(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(22, 18, 22, 18)
            layout.setSpacing(12)

            # ---------------------------------------------------------
            # Título
            # ---------------------------------------------------------
            titulo = QLabel("COBRAR VENTA")
            titulo.setObjectName("titulo_pago")
            titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(titulo)

            # ---------------------------------------------------------
            # Resumen de la venta
            # ---------------------------------------------------------
            tarjeta_resumen = QFrame()
            tarjeta_resumen.setObjectName("tarjeta_pago")
            resumen_layout = QVBoxLayout(tarjeta_resumen)
            resumen_layout.setContentsMargins(16, 12, 16, 12)

            self.etiqueta_subtotal = QLabel()
            self.etiqueta_subtotal.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.etiqueta_subtotal.setStyleSheet(
                "font-size: 16px; font-weight: 700;"
            )
            resumen_layout.addWidget(self.etiqueta_subtotal)

            layout.addWidget(tarjeta_resumen)

            # ---------------------------------------------------------
            # Medios de pago
            # ---------------------------------------------------------
            tarjeta_pago = QFrame()
            tarjeta_pago.setObjectName("tarjeta_pago")

            grid = QGridLayout(tarjeta_pago)
            grid.setContentsMargins(18, 14, 18, 14)
            grid.setHorizontalSpacing(14)
            grid.setVerticalSpacing(10)
            grid.setColumnMinimumWidth(0, 155)
            grid.setColumnStretch(1, 1)

            self.check_combinado = QCheckBox(
                "Combinar dos medios de pago"
            )
            self.check_combinado.setObjectName("pago_combinado")
            self.check_combinado.setEnabled(
                len(self.medios_habilitados) >= 2
            )
            self.check_combinado.stateChanged.connect(
                self._cambiar_modo
            )
            grid.addWidget(self.check_combinado, 0, 0, 1, 2)

            # Primer medio
            self.etiqueta_medio_1 = QLabel("Medio de pago:")
            self.etiqueta_medio_1.setObjectName("etiqueta_formulario")
            self.etiqueta_medio_1.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            self.combo_medio_1 = QComboBox()
            self.combo_medio_2 = QComboBox()

            for medio in self.medios_habilitados:
                self.combo_medio_1.addItem(MEDIOS[medio], medio)
                self.combo_medio_2.addItem(MEDIOS[medio], medio)

            if self.combo_medio_2.count() > 1:
                self.combo_medio_2.setCurrentIndex(1)

            self.combo_medio_1.currentIndexChanged.connect(
                self._cambio_medio_1
            )
            self.combo_medio_2.currentIndexChanged.connect(
                self._cambio_medio_2
            )

            grid.addWidget(self.etiqueta_medio_1, 1, 0)
            grid.addWidget(self.combo_medio_1, 1, 1)

            # Segundo medio
            self.etiqueta_medio_2 = QLabel("Segundo medio:")
            self.etiqueta_medio_2.setObjectName("etiqueta_formulario")
            self.etiqueta_medio_2.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            grid.addWidget(self.etiqueta_medio_2, 2, 0)
            grid.addWidget(self.combo_medio_2, 2, 1)

            # Importe del primer medio
            self.etiqueta_importe_1 = QLabel("Importe primer medio:")
            self.etiqueta_importe_1.setObjectName("etiqueta_formulario")
            self.etiqueta_importe_1.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            self.campo_importe_1 = QLineEdit()
            self.campo_importe_1.setPlaceholderText(
                "Ingresá el importe"
            )
            self.campo_importe_1.textChanged.connect(
                self._actualizar_resumen
            )

            grid.addWidget(self.etiqueta_importe_1, 3, 0)
            grid.addWidget(self.campo_importe_1, 3, 1)

            # Importe automático del segundo medio
            self.etiqueta_titulo_importe_2 = QLabel(
                "Importe segundo medio:"
            )
            self.etiqueta_titulo_importe_2.setObjectName(
                "etiqueta_formulario"
            )
            self.etiqueta_titulo_importe_2.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            self.etiqueta_importe_2 = QLabel("$0,00")
            self.etiqueta_importe_2.setStyleSheet(
                """
                background: #eef2f6;
                border: 1px solid #cbd5e1;
                border-radius: 7px;
                padding: 9px 10px;
                font-weight: 800;
                """
            )

            grid.addWidget(self.etiqueta_titulo_importe_2, 4, 0)
            grid.addWidget(self.etiqueta_importe_2, 4, 1)

            # Cuotas
            self.etiqueta_cuotas = QLabel("Cuotas:")
            self.etiqueta_cuotas.setObjectName("etiqueta_formulario")
            self.etiqueta_cuotas.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            self.combo_cuotas = QComboBox()
            self.combo_cuotas.addItems(["1", "3", "6", "12"])
            self.combo_cuotas.currentIndexChanged.connect(
                self._actualizar_resumen
            )

            grid.addWidget(self.etiqueta_cuotas, 5, 0)
            grid.addWidget(self.combo_cuotas, 5, 1)

            self.check_cigarrillos_efectivo = QCheckBox(
                "Cobrar los cigarrillos en efectivo, sin recargo"
            )
            self.check_cigarrillos_efectivo.stateChanged.connect(
                self._actualizar_resumen
            )
            grid.addWidget(
                self.check_cigarrillos_efectivo,
                6,
                0,
                1,
                2,
            )

            layout.addWidget(tarjeta_pago)

            # ---------------------------------------------------------
            # Efectivo y vuelto
            # ---------------------------------------------------------
            self.panel_efectivo = QFrame()
            self.panel_efectivo.setObjectName("tarjeta_pago")

            efectivo_grid = QGridLayout(self.panel_efectivo)
            efectivo_grid.setContentsMargins(18, 12, 18, 12)
            efectivo_grid.setHorizontalSpacing(14)
            efectivo_grid.setVerticalSpacing(8)
            efectivo_grid.setColumnMinimumWidth(0, 155)
            efectivo_grid.setColumnStretch(1, 1)

            etiqueta_recibido = QLabel("Efectivo recibido:")
            etiqueta_recibido.setObjectName("etiqueta_formulario")
            etiqueta_recibido.setAlignment(
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )

            self.campo_monto_recibido = QLineEdit()
            self.campo_monto_recibido.setPlaceholderText(
                "Dinero entregado por el cliente"
            )
            self.campo_monto_recibido.textChanged.connect(
                self._actualizar_resumen
            )

            self.etiqueta_vuelto = QLabel("Vuelto: $0,00")
            self.etiqueta_vuelto.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.etiqueta_vuelto.setStyleSheet(
                """
                background: #dcf7e7;
                color: #079447;
                border: 1px solid #a7e5bf;
                border-radius: 7px;
                padding: 8px;
                font-size: 18px;
                font-weight: 900;
                """
            )

            efectivo_grid.addWidget(etiqueta_recibido, 0, 0)
            efectivo_grid.addWidget(self.campo_monto_recibido, 0, 1)
            efectivo_grid.addWidget(
                self.etiqueta_vuelto,
                1,
                0,
                1,
                2,
            )

            layout.addWidget(self.panel_efectivo)

            # ---------------------------------------------------------
            # Recargos y total
            # ---------------------------------------------------------
            self.etiqueta_detalle = QLabel()
            self.etiqueta_detalle.setWordWrap(True)
            self.etiqueta_detalle.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.etiqueta_detalle.setStyleSheet(
                "color:#9a5b04; font-weight:600;"
            )
            layout.addWidget(self.etiqueta_detalle)

            self.etiqueta_total = QLabel()
            self.etiqueta_total.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.etiqueta_total.setStyleSheet(
                """
                background: #ffffff;
                color: #079447;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                padding: 12px;
                font-size: 25px;
                font-weight: 900;
                """
            )
            layout.addWidget(self.etiqueta_total)

            self.check_imprimir_ticket = QCheckBox(
                "Imprimir ticket al confirmar la venta"
            )
            try:
                impresora_configurada = bool(
                    obtener_configuracion_comercio().get("impresora")
                )
            except Exception:
                impresora_configurada = False
            self.check_imprimir_ticket.setChecked(impresora_configurada)
            self.check_imprimir_ticket.setEnabled(impresora_configurada)
            if impresora_configurada:
                self.check_imprimir_ticket.setToolTip(
                    "Desmarcá esta opción si el cliente no desea ticket impreso."
                )
            else:
                self.check_imprimir_ticket.setText(
                    "Ticket sin imprimir (no hay impresora configurada)"
                )
                self.check_imprimir_ticket.setToolTip(
                    "Podés configurar la impresora más adelante."
                )
            layout.addWidget(self.check_imprimir_ticket)

            # ---------------------------------------------------------
            # Botones
            # ---------------------------------------------------------
            botones = QHBoxLayout()
            botones.setSpacing(10)
            botones.addStretch()

            cancelar = QPushButton("Cancelar")
            cancelar.setMinimumWidth(110)
            cancelar.clicked.connect(self.reject)

            confirmar = QPushButton("Confirmar cobro")
            confirmar.setObjectName("confirmar")
            confirmar.setMinimumWidth(155)
            confirmar.setDefault(True)
            confirmar.clicked.connect(self._confirmar)

            botones.addWidget(cancelar)
            botones.addWidget(confirmar)
            layout.addLayout(botones)

    @staticmethod
    def _convertir_monto(texto):
        if not str(texto or "").strip():
            return 0.0
        return convertir_decimal_finito(
            texto,
            nombre="El importe",
            minimo=0,
            maximo=100000000,
            interpretar_punto_miles=True,
        )

    def _es_combinado(self):
        return self.check_combinado.isChecked()

    def _medios(self):
        primero = self.combo_medio_1.currentData()
        if not self._es_combinado():
            return [primero]
        return [primero, self.combo_medio_2.currentData()]

    def _cambio_medio_1(self, _indice=None):
        if (
            self._es_combinado()
            and self.combo_medio_1.currentData()
            == self.combo_medio_2.currentData()
        ):
            siguiente = (
                self.combo_medio_2.currentIndex() + 1
            ) % self.combo_medio_2.count()
            self.combo_medio_2.blockSignals(True)
            self.combo_medio_2.setCurrentIndex(siguiente)
            self.combo_medio_2.blockSignals(False)
        self._actualizar_resumen()

    def _cambio_medio_2(self, _indice=None):
        if (
            self._es_combinado()
            and self.combo_medio_1.currentData()
            == self.combo_medio_2.currentData()
        ):
            QMessageBox.information(
                self,
                "Elegí otro medio",
                "Los dos medios del pago combinado deben ser distintos.",
            )
        self._actualizar_resumen()

    def _cambiar_modo(self, _estado=None):
        if self._es_combinado():
            self._cambio_medio_1()
        self._actualizar_resumen()

    def _calcular_importes(self):
        medios = set(self._medios())
        cigarrillos_efectivo = (
            self.check_cigarrillos_efectivo.isChecked()
        )
        recargo_cigarrillos = 0.0
        if (
            self.subtotal_cigarrillos > 0
            and medios & MEDIOS_ELECTRONICOS
            and not cigarrillos_efectivo
        ):
            recargo_cigarrillos = round(
                self.subtotal_cigarrillos
                * float(self.configuracion.get("recargo_cigarrillos", 0.15)),
                2,
            )
        subtotal_con_descuento = round(
            max(self.subtotal - self.descuento_promociones, 0),
            2,
        )
        recargo_credito = 0.0
        if "CREDITO" in medios:
            recargo_credito = round(
                subtotal_con_descuento
                * float(self.configuracion.get("recargo_credito", 0.15)),
                2,
            )
        total = round(
            subtotal_con_descuento
            + recargo_cigarrillos
            + recargo_credito,
            2,
        )
        return recargo_cigarrillos, recargo_credito, total

    def _importe_segundo(self, total):
        try:
            primero = self._convertir_monto(self.campo_importe_1.text())
        except ValueError:
            return None
        return round(total - primero, 2)

    def _importe_efectivo(self, total):
        medios = self._medios()
        if "EFECTIVO" not in medios:
            return 0.0
        if not self._es_combinado():
            return total
        try:
            primero = self._convertir_monto(self.campo_importe_1.text())
        except ValueError:
            return 0.0
        segundo = round(total - primero, 2)
        return primero if medios[0] == "EFECTIVO" else segundo

    def _actualizar_resumen(self, _valor=None):
        combinado = self._es_combinado()
        medios = self._medios()
        self.combo_medio_2.setVisible(combinado)
        self.etiqueta_medio_2.setVisible(combinado)
        self.campo_importe_1.setVisible(combinado)
        self.etiqueta_importe_1.setVisible(combinado)
        self.etiqueta_importe_2.setVisible(combinado)
        self.etiqueta_titulo_importe_2.setVisible(combinado)

        hay_efectivo = "EFECTIVO" in medios
        hay_electronico = bool(set(medios) & MEDIOS_ELECTRONICOS)
        mostrar_cigarrillos = (
            self.subtotal_cigarrillos > 0
            and hay_efectivo
            and hay_electronico
        )
        self.check_cigarrillos_efectivo.setVisible(mostrar_cigarrillos)
        if not mostrar_cigarrillos:
            self.check_cigarrillos_efectivo.blockSignals(True)
            self.check_cigarrillos_efectivo.setChecked(False)
            self.check_cigarrillos_efectivo.blockSignals(False)

        mostrar_cuotas = "CREDITO" in medios
        self.combo_cuotas.setVisible(mostrar_cuotas)
        self.etiqueta_cuotas.setVisible(mostrar_cuotas)
        self.panel_efectivo.setVisible(hay_efectivo)

        recargo_cigarrillos, recargo_credito, total = (
            self._calcular_importes()
        )
        self.etiqueta_subtotal.setText(
            f"Subtotal de productos: {formatear_moneda(self.subtotal)}"
        )
        self.etiqueta_total.setText(f"TOTAL: {formatear_moneda(total)}")

        detalles = []
        if self.descuento_promociones:
            detalles.append(
                "Descuentos por promociones: -"
                f"{formatear_moneda(self.descuento_promociones)}"
            )
            for aplicacion in self.aplicaciones_promociones:
                detalles.append(
                    f"• {aplicacion['promocion']} "
                    f"x{aplicacion['veces']}: -"
                    f"{formatear_moneda(aplicacion['ahorro'])}"
                )
        if recargo_cigarrillos:
            detalles.append(
                "Recargo cigarrillos: "
                f"{formatear_moneda(recargo_cigarrillos)}"
            )
        if recargo_credito:
            cuotas = int(self.combo_cuotas.currentText())
            detalles.append(
                "Recargo crédito (15%): "
                f"{formatear_moneda(recargo_credito)}"
            )
            detalles.append(
                f"{cuotas} cuota(s) de "
                f"{formatear_moneda(round(total / cuotas, 2))}"
            )
        self.etiqueta_detalle.setText("\n".join(detalles))
        self.etiqueta_detalle.setVisible(bool(detalles))

        if combinado:
            segundo = self._importe_segundo(total)
            self.etiqueta_importe_2.setText(
                "Monto inválido"
                if segundo is None
                else formatear_moneda(segundo)
            )

        if hay_efectivo:
            try:
                recibido = self._convertir_monto(
                    self.campo_monto_recibido.text()
                )
                efectivo_aplicado = self._importe_efectivo(total)
                vuelto = max(round(recibido - efectivo_aplicado, 2), 0)
                self.etiqueta_vuelto.setText(
                    f"Vuelto: {formatear_moneda(vuelto)}"
                )
            except ValueError:
                self.etiqueta_vuelto.setText("Vuelto: monto inválido")

    def _confirmar(self):
        medios = self._medios()
        if (
            self._es_combinado()
            and medios[0] == medios[1]
        ):
            QMessageBox.warning(
                self,
                "Medios repetidos",
                "Elegí dos medios de pago distintos.",
            )
            return

        recargo_cigarrillos, recargo_credito, total = (
            self._calcular_importes()
        )
        importes = {medio: 0.0 for medio in MEDIOS}

        if self._es_combinado():
            try:
                primero = self._convertir_monto(
                    self.campo_importe_1.text()
                )
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Importe inválido",
                    "Ingresá un importe numérico para el primer medio.",
                )
                return
            segundo = round(total - primero, 2)
            if primero <= 0 or segundo <= 0:
                QMessageBox.warning(
                    self,
                    "Importes inválidos",
                    "Cada medio debe cubrir un importe mayor que cero.",
                )
                return
            importes[medios[0]] = primero
            importes[medios[1]] = segundo
        else:
            importes[medios[0]] = total

        monto_recibido = None
        vuelto = 0.0
        efectivo_aplicado = importes["EFECTIVO"]
        if efectivo_aplicado > 0:
            try:
                monto_recibido = self._convertir_monto(
                    self.campo_monto_recibido.text()
                )
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Monto inválido",
                    "Ingresá el efectivo recibido.",
                )
                return
            if monto_recibido < efectivo_aplicado:
                QMessageBox.warning(
                    self,
                    "Efectivo insuficiente",
                    "El efectivo recibido debe cubrir "
                    f"{formatear_moneda(efectivo_aplicado)}.",
                )
                return
            vuelto = round(monto_recibido - efectivo_aplicado, 2)

        if (
            self.check_cigarrillos_efectivo.isChecked()
            and efectivo_aplicado < self.subtotal_cigarrillos
        ):
            QMessageBox.warning(
                self,
                "Efectivo insuficiente",
                "La parte en efectivo debe cubrir los cigarrillos: "
                f"{formatear_moneda(self.subtotal_cigarrillos)}.",
            )
            return

        cuotas = (
            int(self.combo_cuotas.currentText())
            if "CREDITO" in medios
            else None
        )
        self.resultado_pago = {
            "forma_pago": (
                "COMBINADO" if self._es_combinado() else medios[0]
            ),
            "monto_efectivo": importes["EFECTIVO"],
            "monto_qr": importes["QR"],
            "monto_debito": importes["DEBITO"],
            "monto_credito": importes["CREDITO"],
            "monto_recibido": monto_recibido,
            "vuelto": vuelto,
            "cigarrillos_en_efectivo": (
                self.check_cigarrillos_efectivo.isChecked()
            ),
            "cuotas": cuotas,
            "total": total,
            "recargo": round(
                recargo_cigarrillos + recargo_credito,
                2,
            ),
            "descuento_promociones": self.descuento_promociones,
            "aplicaciones_promociones": self.aplicaciones_promociones,
            "imprimir_ticket": self.check_imprimir_ticket.isChecked(),
        }
        self.accept()
