import json
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services.auditoria_service import (
    listar_acciones_auditoria,
    listar_auditorias,
)
from services.usuario_service import listar_usuarios
from ui.estilos import ESTILO_GLOBAL


OPCIONES_PERIODO = [
    "Todo el historial",
    "Hoy",
    "Esta semana",
    "Este mes",
]


class VentanaAuditoria(QWidget):
    def __init__(self, usuario):
        super().__init__()

        self.usuario = usuario
        self.registros = []

        self.setWindowTitle("NEPOS — Auditoría")
        self.resize(1200, 760)
        self.setMinimumSize(980, 650)
        self.setStyleSheet(ESTILO_GLOBAL)

        self._armar_interfaz()
        self._cargar_filtros()
        self.buscar()

    def _armar_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)

        cabecera = QFrame()
        cabecera.setObjectName("tarjeta")
        fila_cabecera = QHBoxLayout(cabecera)

        textos = QVBoxLayout()
        titulo = QLabel("AUDITORÍA")
        titulo.setObjectName("titulo_modulo")
        subtitulo = QLabel(
            "Historial de operaciones relevantes. "
            "Los registros son solo lectura."
        )
        subtitulo.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        fila_cabecera.addLayout(textos)
        fila_cabecera.addStretch()
        layout.addWidget(cabecera)

        filtros = QFrame()
        filtros.setObjectName("tarjeta")
        fila_filtros = QHBoxLayout(filtros)

        self.combo_periodo = QComboBox()
        self.combo_periodo.addItems(OPCIONES_PERIODO)
        self.combo_periodo.currentTextChanged.connect(self.buscar)

        self.combo_usuario = QComboBox()
        self.combo_usuario.currentIndexChanged.connect(self.buscar)

        self.combo_accion = QComboBox()
        self.combo_accion.currentIndexChanged.connect(self.buscar)

        boton_actualizar = QPushButton("Actualizar")
        boton_actualizar.clicked.connect(self.buscar)

        fila_filtros.addWidget(QLabel("Período:"))
        fila_filtros.addWidget(self.combo_periodo)
        fila_filtros.addWidget(QLabel("Usuario:"))
        fila_filtros.addWidget(self.combo_usuario)
        fila_filtros.addWidget(QLabel("Acción:"))
        fila_filtros.addWidget(self.combo_accion)
        fila_filtros.addWidget(boton_actualizar)
        fila_filtros.addStretch()
        layout.addWidget(filtros)

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            [
                "Fecha y hora",
                "Usuario",
                "Acción",
                "Entidad",
                "Turno",
                "Venta",
                "Nivel",
            ]
        )
        self.tabla.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )
        self.tabla.itemSelectionChanged.connect(
            self._mostrar_detalle
        )
        layout.addWidget(self.tabla, 2)

        layout.addWidget(QLabel("Detalle del registro seleccionado:"))

        self.detalle = QTextEdit()
        self.detalle.setReadOnly(True)
        self.detalle.setPlaceholderText(
            "Seleccioná un registro para ver su detalle."
        )
        self.detalle.setMinimumHeight(150)
        layout.addWidget(self.detalle)

    def _cargar_filtros(self):
        self.combo_usuario.blockSignals(True)
        self.combo_usuario.clear()
        self.combo_usuario.addItem("Todos", None)

        for usuario in listar_usuarios(
            self.usuario.id,
            estado="TODOS",
        ):
            self.combo_usuario.addItem(
                usuario.nombre or usuario.usuario,
                usuario.id,
            )

        self.combo_usuario.blockSignals(False)

        self.combo_accion.blockSignals(True)
        self.combo_accion.clear()
        self.combo_accion.addItem("Todas", None)

        for accion in listar_acciones_auditoria():
            self.combo_accion.addItem(accion, accion)

        self.combo_accion.blockSignals(False)

    def _rango_fechas(self):
        hoy = date.today()
        periodo = self.combo_periodo.currentText()

        if periodo == "Hoy":
            return hoy, hoy

        if periodo == "Esta semana":
            return hoy - timedelta(days=hoy.weekday()), hoy

        if periodo == "Este mes":
            return hoy.replace(day=1), hoy

        return None, None

    def buscar(self):
        fecha_desde, fecha_hasta = self._rango_fechas()

        self.registros = listar_auditorias(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            usuario_id=self.combo_usuario.currentData(),
            accion=self.combo_accion.currentData(),
        )

        self.tabla.setRowCount(len(self.registros))

        for fila, registro in enumerate(self.registros):
            fecha = (
                registro.fecha.strftime("%d/%m/%Y %H:%M")
                if registro.fecha
                else "—"
            )
            usuario = (
                registro.usuario.nombre
                if registro.usuario
                else "Sistema"
            )

            valores = [
                fecha,
                usuario,
                registro.accion or "—",
                registro.entidad or "—",
                str(registro.turno_id or "—"),
                str(registro.venta_id or "—"),
                registro.nivel or "INFO",
            ]

            for columna, valor in enumerate(valores):
                self.tabla.setItem(
                    fila,
                    columna,
                    QTableWidgetItem(valor),
                )

        self.detalle.clear()

    def _mostrar_detalle(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            return

        registro = self.registros[filas[0].row()]
        detalle = registro.detalle or "Sin detalle adicional."

        try:
            detalle = json.dumps(
                json.loads(detalle),
                ensure_ascii=False,
                indent=2,
            )
        except (TypeError, ValueError):
            pass

        self.detalle.setPlainText(detalle)