from datetime import datetime
from utils.rutas import ruta_icono
from PySide6.QtGui import QPixmap

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QStyle,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.ingreso_service import (
    ErrorIngreso,
    buscar_producto_por_codigo,
    calcular_incremento,
    crear_proveedor,
    listar_proveedores,
    registrar_ingreso_lote,
)
from ui.estilos import (
    ESTILO_GLOBAL,
    configurar_boton_peligro,
    configurar_boton_primario,
)
from utils.formato import formatear_cantidad, formatear_moneda
from utils.validacion import convertir_decimal_finito


class DialogoNuevoProveedor(QDialog):
    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.proveedor_creado = None
        self.setWindowTitle("Nuevo proveedor")
        self.setMinimumWidth(420)

        form = QFormLayout()
        self.campo_nombre = QLineEdit()
        self.campo_telefono = QLineEdit()
        self.campo_mail = QLineEdit()
        self.campo_direccion = QLineEdit()
        form.addRow("Nombre:", self.campo_nombre)
        form.addRow("Teléfono:", self.campo_telefono)
        form.addRow("Mail:", self.campo_mail)
        form.addRow("Dirección:", self.campo_direccion)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self.guardar)
        botones.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Nuevo proveedor</h2>"))
        layout.addLayout(form)
        layout.addWidget(botones)

    def guardar(self):
        try:
            self.proveedor_creado = crear_proveedor(
                nombre=self.campo_nombre.text(),
                telefono=self.campo_telefono.text(),
                mail=self.campo_mail.text(),
                direccion=self.campo_direccion.text(),
                usuario_id=self.usuario.id,
            )
        except ErrorIngreso as error:
            QMessageBox.warning(
                self, "No se pudo crear", str(error)
            )
            return
        self.accept()


class VentanaIngreso(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.producto_encontrado = None
        self.items = []

        self.setWindowTitle("NEPOS — Ingreso de mercadería")
        self.resize(1120, 790)
        self.setMinimumSize(940, 680)

    
        self.setStyleSheet(ESTILO_GLOBAL)

        self._armar_interfaz()
        self._recargar_proveedores()
        self.campo_codigo.setFocus()

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)

        # =========================================================
        # CABECERA
        # =========================================================
        cabecera = QFrame()
        cabecera.setObjectName("tarjeta")

        fila_cabecera = QHBoxLayout(cabecera)
        fila_cabecera.setContentsMargins(18, 10, 18, 10)

        icono_titulo = QLabel()

        archivo_icono = ruta_icono("ingreso_mercaderia.png")
        
        pixmap = QPixmap(str(archivo_icono))
        
        icono_titulo.setPixmap(
            pixmap.scaled(
                34,
                34,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        icono_titulo.setFixedSize(40, 40)
        icono_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        titulo = QLabel("INGRESO DE MERCADERÍA")
        titulo.setObjectName("titulo_modulo")
        
        fila_cabecera.addWidget(icono_titulo)
        fila_cabecera.addWidget(titulo)

        fila_cabecera.addStretch()

        fecha = QLabel(
            f"<b>FECHA</b><br>"
            f"{datetime.now().strftime('%d/%m/%Y')}"
        )
        fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fila_cabecera.addWidget(fecha)

        layout.addWidget(cabecera)

        # =========================================================
        # FORMULARIO DE CARGA
        # =========================================================
        datos = QFrame()
        datos.setObjectName("tarjeta")

        grid = QGridLayout(datos)
        grid.setContentsMargins(16, 12, 16, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(7)

        # ---------------------------------------------------------
        # Proveedor de la factura
        # ---------------------------------------------------------
        etiqueta_proveedor = QLabel("Proveedor de la factura")
        grid.addWidget(etiqueta_proveedor, 0, 0)

        self.combo_proveedor = QComboBox()
        self.combo_proveedor.setMinimumHeight(44)
        grid.addWidget(
            self.combo_proveedor,
            1,
            0,
            1,
            5,
        )

        self.boton_nuevo_proveedor = QPushButton(
            "＋ Nuevo proveedor"
        )
        self.boton_nuevo_proveedor.setObjectName(
            "nuevo_proveedor"
        )
        self.boton_nuevo_proveedor.setMinimumHeight(44)
        self.boton_nuevo_proveedor.setVisible(
            self.usuario.rol in ("ADMIN", "SUPERVISOR")
        )
        self.boton_nuevo_proveedor.clicked.connect(
            self.abrir_nuevo_proveedor
        )

        grid.addWidget(
            self.boton_nuevo_proveedor,
            1,
            5,
            1,
            2,
        )

        # ---------------------------------------------------------
        # Código de barras
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Código de barras"),
            2,
            0,
        )

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText(
            "Escaneá o ingresá el código"
        )
        self.campo_codigo.setMinimumHeight(44)
        self.campo_codigo.returnPressed.connect(self.buscar)

        grid.addWidget(
            self.campo_codigo,
            3,
            0,
            1,
            2,
        )

        boton_buscar = QPushButton("🔍  Buscar")
        boton_buscar.setObjectName("buscar_ingreso")
        boton_buscar.setFixedWidth(125)
        boton_buscar.setMinimumHeight(44)
        boton_buscar.clicked.connect(self.buscar)

        grid.addWidget(
            boton_buscar,
            3,
            2,
        )

        # ---------------------------------------------------------
        # Producto encontrado
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Producto encontrado"),
            2,
            3,
        )

        self.etiqueta_producto = QLabel(
            "Esperando producto…"
        )
        self.etiqueta_producto.setObjectName(
            "producto_encontrado_ingreso"
        )
        self.etiqueta_producto.setMinimumHeight(44)
        self.etiqueta_producto.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        grid.addWidget(
            self.etiqueta_producto,
            3,
            3,
            1,
            2,
        )

        # ---------------------------------------------------------
        # Cantidad
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Cantidad"),
            2,
            5,
        )

        self.campo_cantidad = QLineEdit("1")
        self.campo_cantidad.setMinimumHeight(44)
        self.campo_cantidad.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        grid.addWidget(
            self.campo_cantidad,
            3,
            5,
            1,
            2,
        )

        # ---------------------------------------------------------
        # Costo unitario
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Costo unitario"),
            4,
            0,
        )

        self.campo_costo = QLineEdit()
        self.campo_costo.setPlaceholderText(
            "Costo según factura"
        )
        self.campo_costo.setMinimumHeight(44)
        self.campo_costo.textChanged.connect(
            self._actualizar_margen
        )

        grid.addWidget(
            self.campo_costo,
            5,
            0,
            1,
            2,
        )

        # ---------------------------------------------------------
        # Precio de venta
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Precio de venta"),
            4,
            2,
        )

        self.campo_precio = QLineEdit()
        self.campo_precio.setPlaceholderText(
            "Precio al público"
        )
        self.campo_precio.setMinimumHeight(44)
        self.campo_precio.textChanged.connect(
            self._actualizar_margen
        )

        grid.addWidget(
            self.campo_precio,
            5,
            2,
            1,
            2,
        )

        # ---------------------------------------------------------
        # Margen calculado
        # ---------------------------------------------------------
        grid.addWidget(
            QLabel("Margen calculado"),
            4,
            4,
        )

        self.etiqueta_margen = QLabel("—")
        self.etiqueta_margen.setObjectName(
            "margen_ingreso"
        )
        self.etiqueta_margen.setMinimumHeight(44)
        self.etiqueta_margen.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        grid.addWidget(
            self.etiqueta_margen,
            5,
            4,
        )

        # ---------------------------------------------------------
        # Botón agregar
        # ---------------------------------------------------------
        boton_agregar = QPushButton("＋  AGREGAR PRODUCTO")
        boton_agregar.setObjectName("agregar_ingreso")
        boton_agregar.setMinimumHeight(44)
        boton_agregar.clicked.connect(self.agregar)

        grid.addWidget(
            boton_agregar,
            5,
            5,
            1,
            2,
        )

        # Navegación con Enter
        self.campo_cantidad.returnPressed.connect(
            self.campo_costo.setFocus
        )
        self.campo_costo.returnPressed.connect(
            self.campo_precio.setFocus
        )
        self.campo_precio.returnPressed.connect(
            self.agregar
        )

        # ---------------------------------------------------------
        # Grupo de productos
        # ---------------------------------------------------------
        self.etiqueta_grupo = QLabel("")
        self.etiqueta_grupo.setObjectName("grupo_ingreso")
        self.etiqueta_grupo.setWordWrap(True)
        self.etiqueta_grupo.setMinimumHeight(30)

        grid.addWidget(
            self.etiqueta_grupo,
            6,
            0,
            1,
            4,
        )

        self.check_aplicar_grupo = QCheckBox(
            "Actualizar costo y precio de todo el grupo"
        )
        self.check_aplicar_grupo.setVisible(False)

        grid.addWidget(
            self.check_aplicar_grupo,
            6,
            4,
            1,
            3,
        )

        # Distribución del ancho
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 2)
        grid.setColumnStretch(4, 2)
        grid.setColumnStretch(5, 1)
        grid.setColumnStretch(6, 1)

        layout.addWidget(datos)

        # =========================================================
        # TABLA DE PRODUCTOS
        # =========================================================
        tabla_frame = QFrame()
        tabla_frame.setObjectName("tarjeta")

        layout_tabla = QVBoxLayout(tabla_frame)
        layout_tabla.setContentsMargins(6, 6, 6, 6)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            [
                "CÓDIGO",
                "PRODUCTO",
                "CANTIDAD",
                "COSTO",
                "PRECIO VENTA",
                "MARGEN",
                "GRUPO",
                "PROPAGAR",
            ]
        )

        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabla.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(38)
        self.tabla.cellDoubleClicked.connect(self.editar_fila)

        header = self.tabla.horizontalHeader()
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
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        header.setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.Stretch,
        )
        header.setSectionResizeMode(
            7,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        layout_tabla.addWidget(self.tabla)
        layout.addWidget(tabla_frame, 1)

        # =========================================================
        # ACCIONES INFERIORES
        # =========================================================
        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        boton_borrar = QPushButton(
            "✕  BORRAR SELECCIONADO"
        )
        boton_borrar.setObjectName("borrar_ingreso")
        boton_borrar.setMinimumHeight(46)
        boton_borrar.clicked.connect(
            self.borrar_seleccionado
        )

        acciones.addWidget(boton_borrar)
        acciones.addStretch()

        self.etiqueta_resumen = QLabel("0 productos")
        self.etiqueta_resumen.setObjectName(
            "resumen_ingreso"
        )
        acciones.addWidget(self.etiqueta_resumen)

        boton_guardar = QPushButton("GUARDAR INGRESO")
        boton_guardar.setObjectName("guardar_ingreso")

        icono_guardar = self.style().standardIcon(
            QStyle.StandardPixmap.SP_DialogSaveButton
        )
        boton_guardar.setIcon(icono_guardar)
        boton_guardar.setIconSize(QSize(22, 22))

        boton_guardar.setMinimumSize(210, 50)
        boton_guardar.clicked.connect(self.guardar)
        
        acciones.addWidget(boton_guardar)

        layout.addLayout(acciones)

    @staticmethod
    def _numero(texto, moneda=False):
        return convertir_decimal_finito(
            texto,
            nombre="El valor",
            maximo=100000000,
            decimales=3 if not moneda else 2,
            interpretar_punto_miles=moneda,
        )

    def _recargar_proveedores(self):
        seleccionado = self.combo_proveedor.currentData()
        self.combo_proveedor.clear()
        self.combo_proveedor.addItem("Sin proveedor", None)
        for proveedor in listar_proveedores():
            self.combo_proveedor.addItem(
                proveedor.nombre, proveedor.id
            )
        indice = self.combo_proveedor.findData(seleccionado)
        if indice >= 0:
            self.combo_proveedor.setCurrentIndex(indice)

    def abrir_nuevo_proveedor(self):
        dialogo = DialogoNuevoProveedor(self.usuario, self)
        if (
            dialogo.exec() == QDialog.DialogCode.Accepted
            and dialogo.proveedor_creado
        ):
            self._recargar_proveedores()
            indice = self.combo_proveedor.findData(
                dialogo.proveedor_creado.id
            )
            if indice >= 0:
                self.combo_proveedor.setCurrentIndex(indice)

    def buscar(self):
        codigo = self.campo_codigo.text().strip()
        if not codigo:
            return
        self.producto_encontrado = buscar_producto_por_codigo(codigo)
        if not self.producto_encontrado:
            QMessageBox.warning(
                self,
                "Producto no registrado",
                f"No existe un producto con código '{codigo}'.\n"
                "Crealo como producto provisorio desde Caja o solicitá "
                "el alta a un supervisor.",
            )
            return

        producto = self.producto_encontrado
        self.etiqueta_producto.setText(producto.descripcion)
        self.campo_costo.setText(
            str(float(producto.costo or 0)).replace(".", ",")
        )
        self.campo_precio.setText(
            str(float(producto.precio or 0)).replace(".", ",")
        )
        grupo = (
            producto.grupo_precio_rel.nombre
            if producto.grupo_precio_rel
            else ""
        )
        self.check_aplicar_grupo.setVisible(bool(grupo))
        self.check_aplicar_grupo.setChecked(bool(grupo))
        self.check_aplicar_grupo.setEnabled(False)
        self.check_aplicar_grupo.setText(
            "Actualizar costo y precio de todo el grupo"
        )
        self.etiqueta_grupo.setText(
            f"Grupo de precios: {grupo}"
            if grupo
            else "Sin grupo de precios asignado"
        )
        self.campo_cantidad.selectAll()
        self.campo_cantidad.setFocus()
        self._actualizar_margen()

    def _actualizar_margen(self):
        try:
            costo = self._numero(self.campo_costo.text(), moneda=True)
            precio = self._numero(self.campo_precio.text(), moneda=True)
            margen = calcular_incremento(costo, precio) * 100
            self.etiqueta_margen.setText(f"{margen:.2f}%")
            color = "#079447" if margen >= 0 else "#b42318"
            self.etiqueta_margen.setStyleSheet(
                f"font-size:16px; font-weight:900; color:{color};"
            )
        except ValueError:
            self.etiqueta_margen.setText("—")

    def agregar(self):
        if not self.producto_encontrado:
            QMessageBox.information(
                self,
                "Buscá un producto",
                "Escaneá o buscá un producto antes de agregarlo.",
            )
            return
        try:
            cantidad = self._numero(self.campo_cantidad.text())
            costo = self._numero(self.campo_costo.text(), moneda=True)
            precio = self._numero(self.campo_precio.text(), moneda=True)
        except ValueError:
            QMessageBox.warning(
                self,
                "Datos inválidos",
                "Cantidad, costo y precio deben ser numéricos.",
            )
            return
        if cantidad <= 0 or costo <= 0 or precio <= 0:
            QMessageBox.warning(
                self,
                "Datos inválidos",
                "Cantidad, costo y precio deben ser mayores que cero.",
            )
            return
        if precio < costo and self.usuario.rol != "ADMIN":
            QMessageBox.warning(
                self,
                "Precio menor al costo",
                "El precio de venta no puede ser menor que el costo.",
            )
            return

        producto = self.producto_encontrado
        item = {
            "codigo": producto.codigo,
            "descripcion": producto.descripcion,
            "cantidad": cantidad,
            "costo": costo,
            "precio_venta": precio,
            "grupo_precio": (
                producto.grupo_precio_rel.nombre
                if producto.grupo_precio_rel
                else ""
            ),
            "aplicar_grupo": (
                producto.grupo_precio_id is not None
            ),
        }
        existente = next(
            (
                indice
                for indice, actual in enumerate(self.items)
                if actual["codigo"] == producto.codigo
            ),
            None,
        )
        if existente is None:
            self.items.append(item)
        else:
            self.items[existente] = item
        self._refrescar_tabla()
        self._limpiar_carga()

    def _limpiar_carga(self):
        self.producto_encontrado = None
        self.campo_codigo.clear()
        self.campo_cantidad.setText("1")
        self.campo_costo.clear()
        self.campo_precio.clear()
        self.etiqueta_producto.setText("Esperando producto…")
        self.etiqueta_margen.setText("—")
        self.etiqueta_grupo.clear()
        self.check_aplicar_grupo.setChecked(False)
        self.check_aplicar_grupo.setVisible(False)
        self.check_aplicar_grupo.setEnabled(False)
        self.campo_codigo.setFocus()

    def _refrescar_tabla(self):
        self.tabla.setRowCount(len(self.items))
        total_unidades = 0.0
        for fila, item in enumerate(self.items):
            total_unidades += item["cantidad"]
            margen = calcular_incremento(
                item["costo"], item["precio_venta"]
            )
            valores = [
                item["codigo"],
                item["descripcion"],
                formatear_cantidad(item["cantidad"]),
                formatear_moneda(item["costo"]),
                formatear_moneda(item["precio_venta"]),
                f"{margen * 100:.2f}%",
                item["grupo_precio"] or "—",
                "Sí" if item["aplicar_grupo"] else "No",
            ]
            for columna, valor in enumerate(valores):
                self.tabla.setItem(
                    fila, columna, QTableWidgetItem(str(valor))
                )
        self.etiqueta_resumen.setText(
            f"{len(self.items)} producto(s) — "
            f"{formatear_cantidad(total_unidades)} unidades"
        )

    def borrar_seleccionado(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            QMessageBox.information(
                self, "Elegí un producto", "Seleccioná una fila."
            )
            return
        self.items.pop(filas[0].row())
        self._refrescar_tabla()

    def editar_fila(self, fila, _columna=None):
        if not 0 <= fila < len(self.items):
            return
        item = self.items.pop(fila)
        self._refrescar_tabla()
        self.campo_codigo.setText(item["codigo"])
        self.buscar()
        self.campo_cantidad.setText(
            str(item["cantidad"]).replace(".", ",")
        )
        self.campo_costo.setText(
            str(item["costo"]).replace(".", ",")
        )
        self.campo_precio.setText(
            str(item["precio_venta"]).replace(".", ",")
        )
        self.check_aplicar_grupo.setChecked(
            item["aplicar_grupo"]
        )

    def guardar(self):
        if not self.items:
            QMessageBox.warning(
                self,
                "Ingreso vacío",
                "Agregá al menos un producto.",
            )
            return
        grupos = sorted(
            {
                item["grupo_precio"]
                for item in self.items
                if item["aplicar_grupo"] and item["grupo_precio"]
            }
        )
        texto = (
            f"Productos: {len(self.items)}\n"
            f"Proveedor: {self.combo_proveedor.currentText()}\n"
        )
        if grupos:
            texto += (
                "\nSe actualizarán el costo y el precio de todos los productos "
                f"de estos grupos:\n• {'\n• '.join(grupos)}\n"
            )
        texto += "\n¿Confirmás el ingreso?"
        respuesta = QMessageBox.question(
            self,
            "Confirmar ingreso",
            texto,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            resultado = registrar_ingreso_lote(
                items=self.items,
                proveedor_id=self.combo_proveedor.currentData(),
                usuario_id=self.usuario.id,
            )
        except ErrorIngreso as error:
            QMessageBox.warning(
                self, "No se pudo guardar", str(error)
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self, "Error al guardar", str(error)
            )
            return

        QMessageBox.information(
            self,
            "Ingreso guardado",
            f"Productos ingresados: {resultado['productos']}\n"
            "Otros productos con costo y precio actualizados: "
            f"{resultado['costos_precios_propagados']}",
        )
        self.items = []
        self._refrescar_tabla()
        self._limpiar_carga()