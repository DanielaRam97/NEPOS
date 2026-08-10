from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from services.producto_service import (
    listar_productos_pendientes, aprobar_producto, rechazar_producto, ErrorProducto
)


class DialogoProductosPendientes(QDialog):
    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self._pendientes = []

        self.setWindowTitle("Productos pendientes de aprobación")
        self.resize(700, 500)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3>Productos pendientes</h3>"))

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Código", "Producto", "Categoría", "Cargado por"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        fila_datos = QHBoxLayout()
        self.campo_costo = QLineEdit()
        self.campo_costo.setPlaceholderText("Costo")
        self.campo_incremento = QLineEdit()
        self.campo_incremento.setPlaceholderText("Incremento (%)")
        fila_datos.addWidget(self.campo_costo)
        fila_datos.addWidget(self.campo_incremento)
        layout.addLayout(fila_datos)

        botones = QHBoxLayout()
        boton_aprobar = QPushButton("Aprobar")
        boton_aprobar.clicked.connect(self.aprobar)
        boton_rechazar = QPushButton("Rechazar")
        boton_rechazar.clicked.connect(self.rechazar)
        botones.addWidget(boton_aprobar)
        botones.addWidget(boton_rechazar)
        layout.addLayout(botones)

        self.setLayout(layout)
        self._refrescar()

    def _refrescar(self):
        self._pendientes = listar_productos_pendientes()
        self.tabla.setRowCount(len(self._pendientes))
        for fila, p in enumerate(self._pendientes):
            self.tabla.setItem(fila, 0, QTableWidgetItem(p.codigo))
            self.tabla.setItem(fila, 1, QTableWidgetItem(p.descripcion))
            self.tabla.setItem(fila, 2, QTableWidgetItem(p.categoria_rel.nombre if p.categoria_rel else ""))
            self.tabla.setItem(fila, 3, QTableWidgetItem(p.creado_por.nombre if p.creado_por else "-"))

    def _fila_seleccionada(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            QMessageBox.information(self, "Elegí uno", "Seleccioná un producto de la lista.")
            return None
        return filas[0].row()

    def aprobar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        producto = self._pendientes[fila]

        try:
            costo = float(self.campo_costo.text().replace(",", ".") or "0")
            incremento = float(self.campo_incremento.text().replace(",", ".") or "0") / 100
        except ValueError:
            QMessageBox.warning(self, "Valores inválidos", "Completá costo e incremento con números.")
            return

        try:
            aprobar_producto(
                producto_id=producto.id, usuario_id=self.usuario.id,
                costo=costo, incremento=incremento,
            )
        except ErrorProducto as e:
            QMessageBox.warning(self, "No se pudo aprobar", str(e))
            return

        QMessageBox.information(self, "Aprobado", f"'{producto.descripcion}' ya está disponible para vender.")
        self.campo_costo.clear()
        self.campo_incremento.clear()
        self._refrescar()

    def rechazar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        producto = self._pendientes[fila]

        respuesta = QMessageBox.question(
            self, "Rechazar", f"¿Descartar '{producto.descripcion}'? No se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        try:
            rechazar_producto(producto_id=producto.id, usuario_id=self.usuario.id)
        except ErrorProducto as e:
            QMessageBox.warning(self, "No se pudo rechazar", str(e))
            return

        self._refrescar()