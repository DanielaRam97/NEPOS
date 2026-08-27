from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog
)
from services.suspendida_service import (
    listar_suspendidas, recuperar_suspendida, eliminar_suspendida, ErrorSuspendida
)


class DialogoVentasSuspendidas(QDialog):
    def __init__(self, turno_id, usuario_id, parent=None):
        super().__init__(parent)
        self.turno_id = turno_id
        self.usuario_id = usuario_id
        self.carrito_recuperado = None
        self._suspendidas = []

        self.setWindowTitle("Ventas suspendidas")
        self.resize(560, 420)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3>Ventas suspendidas de este turno</h3>"))

        self.tabla = QTableWidget(0, 3)
        self.tabla.setHorizontalHeaderLabels(["Hora", "Cajero", "Nota"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

        botones = QHBoxLayout()
        boton_recuperar = QPushButton("Recuperar")
        boton_recuperar.clicked.connect(self._recuperar)
        boton_eliminar = QPushButton("Eliminar")
        boton_eliminar.clicked.connect(self._eliminar)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(self.reject)
        botones.addWidget(boton_recuperar)
        botones.addWidget(boton_eliminar)
        botones.addWidget(boton_cerrar)
        layout.addLayout(botones)

        self.setLayout(layout)
        self._refrescar()

    def _refrescar(self):
        try:
            self._suspendidas = listar_suspendidas(
                self.turno_id,
                self.usuario_id,
            )
        except ErrorSuspendida as error:
            QMessageBox.warning(self, "Sin permiso", str(error))
            self._suspendidas = []
        self.tabla.setRowCount(len(self._suspendidas))
        for fila, s in enumerate(self._suspendidas):
            self.tabla.setItem(fila, 0, QTableWidgetItem(s.fecha.strftime("%H:%M")))
            self.tabla.setItem(fila, 1, QTableWidgetItem(s.usuario.nombre if s.usuario else "-"))
            self.tabla.setItem(fila, 2, QTableWidgetItem(s.nota or ""))

    def _fila_seleccionada(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            QMessageBox.information(self, "Elegí una", "Seleccioná una venta suspendida primero.")
            return None
        return filas[0].row()

    def _recuperar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        suspendida = self._suspendidas[fila]
        try:
            self.carrito_recuperado = recuperar_suspendida(
                suspendida.id,
                self.usuario_id,
            )
        except ErrorSuspendida as e:
            QMessageBox.warning(self, "No se pudo recuperar", str(e))
            return
        self.accept()

    def _eliminar(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        suspendida = self._suspendidas[fila]
        respuesta = QMessageBox.question(
            self, "Eliminar", "¿Descartar esta venta suspendida? No se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                motivo, aceptado = QInputDialog.getMultiLineText(
                    self,
                    "Motivo de descarte",
                    "Indicá por qué se descarta esta venta suspendida:",
                )
                
                if not aceptado:
                    return
                
                eliminar_suspendida(
                    suspendida.id,
                    self.usuario_id,
                    motivo,
                )
            except ErrorSuspendida as error:
                QMessageBox.warning(self, "No se pudo eliminar", str(error))
                return
            self._refrescar()

    @staticmethod
    def elegir(turno_id, usuario_id, parent=None):
        dialogo = DialogoVentasSuspendidas(turno_id, usuario_id, parent)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            return dialogo.carrito_recuperado
        return None
