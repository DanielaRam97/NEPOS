from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from services.caja_service import buscar_productos_caja, listar_categorias_caja
from utils.formato import formatear_cantidad, formatear_moneda


class DialogoBuscarProducto(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos = []
        self.producto_seleccionado = None
        self.temporizador_busqueda = QTimer(self)
        self.temporizador_busqueda.setSingleShot(True)
        self.temporizador_busqueda.setInterval(250)
        self.temporizador_busqueda.timeout.connect(self._buscar)
        self.setWindowTitle("Buscar producto")
        self.resize(850, 560)
        self._armar_interfaz()
        self._cargar_categorias()
        self._buscar()
        self.campo_busqueda.setFocus()

    @classmethod
    def buscar(cls, parent=None):
        dialogo = cls(parent)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            return dialogo.producto_seleccionado
        return None

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Buscar producto</h2>"))

        filtros = QHBoxLayout()
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText(
            "Escribí código de barras, código interno, PLU o nombre…"
        )
        self.campo_busqueda.setClearButtonEnabled(True)
        self.campo_busqueda.textEdited.connect(
            self._programar_busqueda
        )
        self.campo_busqueda.returnPressed.connect(self._buscar)
        self.combo_categoria = QComboBox()
        self.combo_categoria.currentIndexChanged.connect(
            self._programar_busqueda
        )
        boton_buscar = QPushButton("🔍  Buscar")
        boton_buscar.setObjectName("primario")
        boton_buscar.clicked.connect(self._buscar)
        filtros.addWidget(self.campo_busqueda, 2)
        filtros.addWidget(self.combo_categoria)
        filtros.addWidget(boton_buscar)
        layout.addLayout(filtros)

        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(
            ["Código", "Producto", "Categoría", "Precio", "Stock"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.tabla.itemSelectionChanged.connect(self._mostrar_detalle)
        self.tabla.cellDoubleClicked.connect(self._aceptar)
        layout.addWidget(self.tabla)

        self.etiqueta_detalle = QLabel(
            "Seleccioná un producto para ver sus datos."
        )
        self.etiqueta_detalle.setWordWrap(True)
        layout.addWidget(self.etiqueta_detalle)

        botones = QHBoxLayout()
        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.clicked.connect(self.reject)
        boton_agregar = QPushButton("Agregar a la venta")
        boton_agregar.setDefault(True)
        boton_agregar.clicked.connect(self._aceptar)
        botones.addStretch()
        botones.addWidget(boton_cancelar)
        botones.addWidget(boton_agregar)
        layout.addLayout(botones)

    def _cargar_categorias(self):
        self.combo_categoria.addItem("Todas las categorías", None)
        for categoria in listar_categorias_caja():
            self.combo_categoria.addItem(categoria.nombre, categoria.id)

    def _programar_busqueda(self, _valor=None):
        """Agrupa pulsaciones rápidas y consulta cuando el usuario pausa."""
        self.temporizador_busqueda.start()

    def _buscar(self):
        self.temporizador_busqueda.stop()
        try:
            self.productos = buscar_productos_caja(
                self.campo_busqueda.text(),
                self.combo_categoria.currentData(),
            )
        except Exception as error:
            QMessageBox.critical(self, "No se pudo buscar", str(error))
            return

        self.tabla.setRowCount(len(self.productos))
        for fila, producto in enumerate(self.productos):
            item_codigo = QTableWidgetItem(producto.codigo)
            item_codigo.setData(Qt.ItemDataRole.UserRole, producto.id)
            self.tabla.setItem(fila, 0, item_codigo)
            self.tabla.setItem(fila, 1, QTableWidgetItem(producto.descripcion))
            categoria = (
                producto.categoria_rel.nombre
                if producto.categoria_rel
                else ""
            )
            self.tabla.setItem(fila, 2, QTableWidgetItem(categoria))
            self.tabla.setItem(
                fila, 3, QTableWidgetItem(formatear_moneda(producto.precio or 0))
            )
            self.tabla.setItem(
                fila, 4, QTableWidgetItem(formatear_cantidad(producto.stock or 0))
            )
        self.etiqueta_detalle.setText(
            f"{len(self.productos)} producto(s) encontrado(s)."
        )
        if self.productos:
            self.tabla.selectRow(0)

    def _fila_seleccionada(self):
        filas = self.tabla.selectionModel().selectedRows()
        return filas[0].row() if filas else None

    def _mostrar_detalle(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        producto = self.productos[fila]
        categoria = (
            producto.categoria_rel.nombre
            if producto.categoria_rel
            else "-"
        )
        revision = (
            "PENDIENTE DE REVISIÓN"
            if getattr(producto, "pendiente_revision", False)
            else "Aprobado"
        )
        self.etiqueta_detalle.setText(
            f"<b>{producto.descripcion}</b><br>"
            f"Código: {producto.codigo} | PLU: {producto.plu or '-'} | "
            f"Categoría: {categoria}<br>"
            f"Precio: {formatear_moneda(producto.precio or 0)} | "
            f"Stock: {formatear_cantidad(producto.stock or 0)} | {revision}"
        )

    def _aceptar(self, _fila=None, _columna=None):
        fila = self._fila_seleccionada()
        if fila is None:
            QMessageBox.information(
                self, "Elegí un producto", "Seleccioná una fila primero."
            )
            return
        self.producto_seleccionado = self.productos[fila]
        self.accept()