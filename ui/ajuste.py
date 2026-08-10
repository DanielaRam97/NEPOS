from utils.rutas import ruta_icono

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.ajuste_service import (
    ErrorAjuste,
    buscar_producto_por_codigo,
    listar_historial,
    registrar_ajuste,
)
from ui.estilos import ESTILO_GLOBAL
from utils.formato import formatear_cantidad



class VentanaAjuste(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.producto_encontrado = None

        self.setWindowTitle("NEPOS — Ajuste de stock")
        self.resize(1000, 740)
        self.setMinimumSize(900, 650)

        # Evita que los estilos grises de Caja reemplacen
        # los colores particulares de esta pestaña.
        self.setStyleSheet(ESTILO_GLOBAL)

        self._armar_interfaz()
        self._refrescar_historial()
        self.campo_codigo.setFocus()

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

        icono_titulo = QLabel()
        archivo_icono = ruta_icono("ajuste_stock.png")

        pixmap = QPixmap(str(archivo_icono))

        if not pixmap.isNull():
            icono_titulo.setPixmap(
                pixmap.scaled(
                    34,
                    34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            # Se muestra solamente si todavía no agregaste el PNG.
            icono_titulo.setText("↕")
            icono_titulo.setStyleSheet(
                "font-size:26px; font-weight:900; color:#4da8da;"
            )

        icono_titulo.setFixedSize(40, 40)
        icono_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setContentsMargins(0, 0, 0, 0)
        bloque_titulo.setSpacing(1)

        titulo = QLabel("AJUSTE DE STOCK")
        titulo.setObjectName("titulo_modulo")

        ayuda = QLabel(
            "Corregí diferencias entre el stock del sistema y "
            "el conteo físico del local."
        )
        ayuda.setObjectName("subtitulo")

        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(ayuda)

        fila_cabecera.addWidget(icono_titulo)
        fila_cabecera.addLayout(bloque_titulo)
        fila_cabecera.addStretch()

        layout.addWidget(cabecera)

        # =====================================================
        # BÚSQUEDA DEL PRODUCTO
        # =====================================================
        bloque_busqueda = QFrame()
        bloque_busqueda.setObjectName("tarjeta")

        grid_busqueda = QGridLayout(bloque_busqueda)
        grid_busqueda.setContentsMargins(16, 11, 16, 11)
        grid_busqueda.setHorizontalSpacing(10)
        grid_busqueda.setVerticalSpacing(5)

        grid_busqueda.addWidget(
            QLabel("Código de barras o código interno"),
            0,
            0,
        )

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText(
            "Escaneá o ingresá el código del producto"
        )
        self.campo_codigo.setMinimumHeight(44)
        self.campo_codigo.returnPressed.connect(self.buscar)

        grid_busqueda.addWidget(
            self.campo_codigo,
            1,
            0,
        )

        boton_buscar = QPushButton("🔍  BUSCAR")
        boton_buscar.setObjectName("buscar_ajuste")
        boton_buscar.setFixedWidth(145)
        boton_buscar.setMinimumHeight(44)
        boton_buscar.clicked.connect(self.buscar)

        grid_busqueda.addWidget(
            boton_buscar,
            1,
            1,
        )

        self.etiqueta_estado = QLabel("")
        self.etiqueta_estado.setObjectName(
            "estado_busqueda_ajuste"
        )
        self.etiqueta_estado.setWordWrap(True)
        self.etiqueta_estado.setVisible(False)

        grid_busqueda.addWidget(
            self.etiqueta_estado,
            2,
            0,
            1,
            2,
        )

        grid_busqueda.setColumnStretch(0, 1)

        layout.addWidget(bloque_busqueda)

        # =====================================================
        # DETALLE DEL AJUSTE
        # =====================================================
        self.bloque_ajuste = QFrame()
        self.bloque_ajuste.setObjectName("tarjeta")

        bloque_layout = QVBoxLayout(self.bloque_ajuste)
        bloque_layout.setContentsMargins(16, 12, 16, 12)
        bloque_layout.setSpacing(10)

        # Producto y stock actual
        fila_producto = QHBoxLayout()
        fila_producto.setSpacing(10)

        self.etiqueta_producto = QLabel(
            "Producto seleccionado"
        )
        self.etiqueta_producto.setObjectName(
            "producto_ajuste"
        )
        self.etiqueta_producto.setMinimumHeight(44)
        self.etiqueta_producto.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.etiqueta_stock_actual = QLabel(
            "Stock actual: —"
        )
        self.etiqueta_stock_actual.setObjectName(
            "stock_actual_ajuste"
        )
        self.etiqueta_stock_actual.setMinimumSize(210, 44)
        self.etiqueta_stock_actual.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        fila_producto.addWidget(
            self.etiqueta_producto,
            1,
        )
        fila_producto.addWidget(
            self.etiqueta_stock_actual,
        )

        bloque_layout.addLayout(fila_producto)

        # Campos del ajuste
        detalle = QGridLayout()
        detalle.setHorizontalSpacing(12)
        detalle.setVerticalSpacing(6)

        detalle.addWidget(
            QLabel("Stock físico contado"),
            0,
            0,
        )
        detalle.addWidget(
            QLabel("Diferencia resultante"),
            0,
            1,
        )

        self.campo_stock_fisico = QLineEdit()
        self.campo_stock_fisico.setPlaceholderText(
            "Cantidad contada físicamente"
        )
        self.campo_stock_fisico.setMinimumHeight(44)
        self.campo_stock_fisico.textChanged.connect(
            self._actualizar_preview
        )

        self.etiqueta_diferencia_preview = QLabel(
            "Sin diferencia"
        )
        self.etiqueta_diferencia_preview.setObjectName(
            "diferencia_ajuste"
        )
        self.etiqueta_diferencia_preview.setMinimumHeight(44)
        self.etiqueta_diferencia_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        detalle.addWidget(
            self.campo_stock_fisico,
            1,
            0,
        )
        detalle.addWidget(
            self.etiqueta_diferencia_preview,
            1,
            1,
        )

        detalle.addWidget(
            QLabel("Motivo del ajuste"),
            2,
            0,
            1,
            2,
        )

        self.campo_motivo = QTextEdit()
        self.campo_motivo.setPlaceholderText(
            "Ej.: conteo físico, rotura, merma, robo o error de carga"
        )
        self.campo_motivo.setFixedHeight(62)

        detalle.addWidget(
            self.campo_motivo,
            3,
            0,
            1,
            2,
        )

        detalle.setColumnStretch(0, 1)
        detalle.setColumnStretch(1, 1)

        bloque_layout.addLayout(detalle)

        # Botón registrar
        fila_registrar = QHBoxLayout()
        fila_registrar.addStretch()

        boton_registrar = QPushButton(
            "REGISTRAR AJUSTE"
        )
        boton_registrar.setObjectName(
            "registrar_ajuste"
        )
        boton_registrar.setMinimumSize(210, 46)

        icono_registrar = self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogApplyButton
        )
        boton_registrar.setIcon(icono_registrar)
        boton_registrar.setIconSize(QSize(21, 21))
        boton_registrar.clicked.connect(self.registrar)

        fila_registrar.addWidget(boton_registrar)
        bloque_layout.addLayout(fila_registrar)

        self.bloque_ajuste.setVisible(False)
        layout.addWidget(self.bloque_ajuste)

        # =====================================================
        # HISTORIAL
        # =====================================================
        historial_frame = QFrame()
        historial_frame.setObjectName("tarjeta")

        historial_layout = QVBoxLayout(historial_frame)
        historial_layout.setContentsMargins(7, 8, 7, 7)
        historial_layout.setSpacing(7)

        titulo_historial = QLabel("HISTORIAL RECIENTE")
        titulo_historial.setObjectName(
            "titulo_historial_ajuste"
        )
        historial_layout.addWidget(titulo_historial)

        self.tabla_historial = QTableWidget(0, 5)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.setHorizontalHeaderLabels(
            [
                "FECHA",
                "PRODUCTO",
                "ANTERIOR → NUEVO",
                "DIFERENCIA",
                "MOTIVO",
            ]
        )
        self.tabla_historial.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_historial.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabla_historial.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla_historial.verticalHeader().setVisible(False)
        self.tabla_historial.verticalHeader().setDefaultSectionSize(
            36
        )

        header = self.tabla_historial.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.Stretch,
        )

        historial_layout.addWidget(self.tabla_historial)

        layout.addWidget(historial_frame, 1)

    def buscar(self):
        codigo = self.campo_codigo.text().strip()

        if not codigo:
            self.etiqueta_estado.setText(
                "Ingresá el código de un producto."
            )
            self.etiqueta_estado.setVisible(True)
            return

        self.producto_encontrado = (
            buscar_producto_por_codigo(codigo)
        )

        if not self.producto_encontrado:
            self.etiqueta_estado.setText(
                f"No existe ningún producto con código '{codigo}'."
            )
            self.etiqueta_estado.setVisible(True)
            self.bloque_ajuste.setVisible(False)
            return

        self.etiqueta_estado.clear()
        self.etiqueta_estado.setVisible(False)

        producto = self.producto_encontrado
        unidad = "kg" if producto.pesable else "unidades"

        self.etiqueta_producto.setText(
            producto.descripcion
        )
        self.etiqueta_stock_actual.setText(
            "Stock actual: "
            f"{formatear_cantidad(producto.stock)} {unidad}"
        )

        self.campo_stock_fisico.setText(
            str(producto.stock).replace(".", ",")
        )
        self.campo_motivo.clear()

        self.bloque_ajuste.setVisible(True)
        self._actualizar_preview()

        self.campo_stock_fisico.setFocus()
        self.campo_stock_fisico.selectAll()

    def _actualizar_preview(self):
        if not self.producto_encontrado:
            return

        try:
            stock_fisico = float(
                (
                    self.campo_stock_fisico.text() or "0"
                ).replace(",", ".")
            )
        except ValueError:
            self.etiqueta_diferencia_preview.setText(
                "Cantidad inválida"
            )
            self.etiqueta_diferencia_preview.setStyleSheet(
                """
                background:#fde8e8;
                color:#b42318;
                border:1px solid #efb4ae;
                border-radius:7px;
                font-weight:800;
                """
            )
            return

        diferencia = round(
            stock_fisico
            - float(self.producto_encontrado.stock or 0),
            3,
        )

        if diferencia > 0:
            self.etiqueta_diferencia_preview.setText(
                f"+{formatear_cantidad(diferencia)} · SOBRANTE"
            )
            self.etiqueta_diferencia_preview.setStyleSheet(
                """
                background:#e4f7eb;
                color:#08783a;
                border:1px solid #a8dfbd;
                border-radius:7px;
                font-weight:900;
                """
            )
        elif diferencia < 0:
            self.etiqueta_diferencia_preview.setText(
                f"{formatear_cantidad(diferencia)} · FALTANTE"
            )
            self.etiqueta_diferencia_preview.setStyleSheet(
                """
                background:#fde8e8;
                color:#b42318;
                border:1px solid #efb4ae;
                border-radius:7px;
                font-weight:900;
                """
            )
        else:
            self.etiqueta_diferencia_preview.setText(
                "SIN DIFERENCIA"
            )
            self.etiqueta_diferencia_preview.setStyleSheet(
                """
                background:#eef2f6;
                color:#64748b;
                border:1px solid #cbd5e1;
                border-radius:7px;
                font-weight:800;
                """
            )

    def registrar(self):
        if not self.producto_encontrado:
            QMessageBox.warning(
                self,
                "Producto requerido",
                "Buscá un producto antes de registrar el ajuste.",
            )
            return

        try:
            stock_fisico = float(
                (
                    self.campo_stock_fisico.text() or "0"
                ).replace(",", ".")
            )
        except ValueError:
            QMessageBox.warning(
                self,
                "Cantidad inválida",
                "El stock físico debe ser numérico.",
            )
            return

        motivo = self.campo_motivo.toPlainText().strip()

        try:
            resultado = registrar_ajuste(
                codigo_producto=(
                    self.producto_encontrado.codigo
                ),
                stock_fisico=stock_fisico,
                motivo=motivo,
                usuario_id=self.usuario.id,
            )
        except ErrorAjuste as error:
            QMessageBox.warning(
                self,
                "No se pudo registrar",
                str(error),
            )
            return

        QMessageBox.information(
            self,
            "Ajuste registrado",
            "Stock actualizado: "
            f"{resultado['stock_anterior']} → "
            f"{resultado['stock_nuevo']}\n"
            "Diferencia: "
            f"{resultado['diferencia']:+.3f}",
        )

        self.producto_encontrado = None
        self.campo_codigo.clear()
        self.campo_stock_fisico.clear()
        self.campo_motivo.clear()
        self.etiqueta_estado.clear()
        self.etiqueta_estado.setVisible(False)
        self.bloque_ajuste.setVisible(False)
        self.campo_codigo.setFocus()

        self._refrescar_historial()

    def _refrescar_historial(self):
        ajustes = listar_historial(limite=30)

        self.tabla_historial.setRowCount(len(ajustes))

        for fila, ajuste in enumerate(ajustes):
            producto_nombre = (
                ajuste.producto.descripcion
                if ajuste.producto
                else "(producto eliminado)"
            )
            usuario_nombre = (
                ajuste.usuario.nombre
                if ajuste.usuario
                else "-"
            )

            valores = [
                ajuste.fecha.strftime("%d/%m/%Y %H:%M"),
                producto_nombre,
                (
                    f"{formatear_cantidad(ajuste.stock_anterior)}"
                    " → "
                    f"{formatear_cantidad(ajuste.stock_nuevo)}"
                ),
                formatear_cantidad(ajuste.diferencia),
                f"{ajuste.motivo} · {usuario_nombre}",
            ]

            for columna, valor in enumerate(valores):
                item = QTableWidgetItem(str(valor))

                if columna in (2, 3):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.tabla_historial.setItem(
                    fila,
                    columna,
                    item,
                )