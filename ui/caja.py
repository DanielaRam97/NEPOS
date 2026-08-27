from datetime import date, datetime

from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QInputDialog,
)

from ui.auditoria import VentanaAuditoria
from ui.dashboard import VentanaDashboard
from ui.auditoria import VentanaAuditoria

from services.exportar_service import (
    exportar_cierre_turno_excel,
    exportar_cierre_turno_pdf,
    )

from services.cierre_service import (
    ErrorCierre,
    calcular_resumen,
    cerrar_turno,
)
from services.venta_service import (
    ErrorVenta,
    buscar_producto,
    buscar_producto_por_plu,
    interpretar_codigo_balanza,
    registrar_venta,
    validar_cantidad,
)
from services.suspendida_service import suspender_venta, ErrorSuspendida
from services.promocion_service import calcular_descuento_promociones
from services.impresion_service import (
    ErrorImpresion,
    imprimir_ticket_venta,
)
from backup_db import hacer_backup
from ui.ajuste import VentanaAjuste
from ui.buscador_producto import DialogoBuscarProducto
from ui.configuracion import VentanaConfiguracion
#from ui.dashboard import VentanaDashboard
from ui.dialogo_pago import DialogoPago
from ui.historial import VentanaHistorial
from ui.ingreso import VentanaIngreso
from ui.producto_pendiente import DialogoProductoPendiente
from ui.productos import VentanaProductos
from ui.usuarios import VentanaUsuarios
from ui.ventas_suspendidas import DialogoVentasSuspendidas
from utils.formato import formatear_cantidad, formatear_moneda
from utils.validacion import convertir_decimal_finito
from ui.promociones import VentanaPromociones
from ui.reportes_cierres import VentanaReportesCierres
from utils.rutas import directorio_cierres, ruta_icono
from version import __version__
from services.configuracion_service import obtener_booleano

# Control temporal de módulos para esta versión.
# Cambiar a True cuando el Dashboard vuelva a habilitarse.
HABILITAR_DASHBOARD = True


ESTILO_GENERAL = """
QWidget#ventana_caja {
    background: #f4f6f8;
    color: #172033;
}
QFrame#contenido {
    background: #ffffff;
    border: 1px solid #cbd2dc;
    border-radius: 12px;
}
QFrame#cabecera, QFrame#entrada, QFrame#panel_inferior {
    background: #ffffff;
    border: 1px solid #cbd2dc;
    border-radius: 12px;
}
QLabel {
    background: transparent;
    color: #172033;
}
QLabel#titulo_nepos {
    background: transparent;
    color: #101827;
    font-family: "Montserrat";
    font-weight: 900;
    padding: 0;
}
QLineEdit {
    background: #ffffff;
    border: 1px solid #aeb8c6;
    border-radius: 7px;
    padding: 8px 10px;
    color: #172033;
    font-size: 13px;
}
QLineEdit:focus {
    border: 2px solid #12a950;
}
QPushButton {
    background: #e5e7eb;
    color: #172033;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 12px;
}
QPushButton:hover {
    background: #d5d9df;
}
QPushButton#primario {
    background: #12aa52;
    color: white;
    font-weight: 800;
}
QPushButton#primario:hover {
    background: #0d9245;
}
QPushButton#agregar_grande {
    background: #12aa52;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 16px;
    font-weight: 900;
}

QPushButton#agregar_grande:hover {
    background: #0d9245;
}

QPushButton#agregar_grande:pressed {
    background: #087d3a;
}
QPushButton#pestana_activa {
    background: #12aa52;
    color: white;
    font-weight: 700;
}
QPushButton#accion_editar {
    background: #f4d45e;
    color: #172033;
    font-weight: 800;
}
QPushButton#accion_editar:hover {
    background: #e9c845;
}
QPushButton#accion_buscar {
    background: #66df8b;
    color: #103c21;
    font-weight: 800;
}
QPushButton#accion_buscar:hover {
    background: #4fd276;
}
QPushButton#accion_vaciar {
    background: #72bce8;
    color: #12364d;
    font-weight: 800;
}
QPushButton#accion_vaciar:hover {
    background: #5baddd;
}
QPushButton#accion_quitar {
    background: #ef8a78;
    color: #5f2118;
    font-weight: 800;
}
QPushButton#accion_quitar:hover {
    background: #e67864;
}
QPushButton#cierre_turno {
    background: #ef8a78;
    color: #5f2118;
    border: 1px solid #df7766;
    border-radius: 16px;
    font-weight: 900;
}
QPushButton#cierre_turno:hover {
    background: #e67864;
}
QLabel#ultimo_nombre {
    background: #6cc58d;
    color: #0e2617;
    border: 1px solid #53ae75;
    border-radius: 17px;
    padding: 6px 16px;
    font-size: 19px;
    font-weight: 900;
}
QLabel#ultimo_precio {
    background: #ffd75e;
    color: #241a00;
    border: 1px solid #d9ad25;
    border-radius: 17px;
    padding: 6px 18px;
    font-size: 19px;
    font-weight: 900;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #edf0f3;
    border: 1px solid #cbd2dc;
    border-radius: 8px;
    color: #172033;
    gridline-color: #e0e4e9;
}
QHeaderView::section {
    background: #ffffff;
    color: #172033;
    border: none;
    border-bottom: 1px solid #cbd2dc;
    padding: 9px;
    font-weight: 700;
}
"""


class VentanaCaja(QWidget):
    def __init__(self, usuario, turno, al_cerrar_turno=None):
        super().__init__()
        self.usuario = usuario
        self.turno = turno
        self.es_dueno_turno = usuario.id == turno.usuario_id
        self.al_cerrar_turno = al_cerrar_turno
        self.carrito = []
        self.descuento_promociones = 0.0
        self.aplicaciones_promociones = []
        self.paginas = {}
        self.botones_navegacion = {}

        self.setObjectName("ventana_caja")
        self.setWindowTitle(f"NEPOS {__version__} — Sistema de cobro")
        self.resize(1120, 790)
        self.setMinimumSize(950, 700)
        self.setStyleSheet(ESTILO_GENERAL)

        self._armar_interfaz()
        self._iniciar_reloj()

    def _armar_interfaz(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(18, 14, 18, 18)
        exterior.setSpacing(7)

        contenido = QFrame()
        contenido.setObjectName("contenido")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(9)
        exterior.addWidget(contenido)

        layout.addLayout(self._crear_navegacion())

        self.contenedor_paginas = QStackedWidget()
        layout.addWidget(self.contenedor_paginas, 1)

        self._crear_paginas()
        self.mostrar_pagina("caja")

    def _crear_pagina_caja(self):
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)

        layout.addWidget(self._crear_cabecera())
        layout.addWidget(self._crear_entrada())

        self.tabla = QTableWidget(0, 5)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setHorizontalHeaderLabels(
            [
                "CÓDIGO",
                "DESCRIPCIÓN",
                "CANTIDAD",
                "PRECIO UNITARIO",
                "SUBTOTAL",
            ]
        )
        self.tabla.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.tabla.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Fixed
        )
        self.tabla.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.tabla.horizontalHeader().setStyleSheet(
            "QHeaderView::section { padding: 8px 10px; font-size: 12px; }"
        )
        self.tabla.cellDoubleClicked.connect(self.editar_cantidad)
        self.campo_codigo.installEventFilter(self)
        self.campo_cantidad.installEventFilter(self)
        self.tabla.installEventFilter(self)
        layout.addWidget(self.tabla, 1)

        acciones = QHBoxLayout()
        acciones.setSpacing(8)
        acciones.setContentsMargins(0, 0, 0, 0)
        boton_editar = QPushButton("F1 · Editar cantidad")
        boton_editar.setObjectName("accion_editar")
        boton_editar.setShortcut(QKeySequence("F1"))
        boton_editar.clicked.connect(self.editar_cantidad)

        boton_buscar = QPushButton("F2 · Buscar producto")
        boton_buscar.setObjectName("accion_buscar")
        boton_buscar.setShortcut(QKeySequence("F2"))
        boton_buscar.clicked.connect(self.buscar_por_nombre)

        boton_vaciar = QPushButton("F3 · Vaciar carrito")
        boton_vaciar.setObjectName("accion_vaciar")
        boton_vaciar.setShortcut(QKeySequence("F3"))
        boton_vaciar.clicked.connect(self.vaciar_carrito)

        boton_quitar = QPushButton("Supr · Quitar producto")
        boton_quitar.setObjectName("accion_quitar")
        boton_quitar.setShortcut(QKeySequence("Delete"))
        boton_quitar.clicked.connect(self.quitar_producto)

        acciones.addWidget(boton_editar)
        acciones.addWidget(boton_buscar)
        acciones.addWidget(boton_vaciar)
        acciones.addWidget(boton_quitar)

        boton_suspender = QPushButton("Suspender venta")
        boton_suspender.clicked.connect(self.suspender_venta_actual)
        acciones.addWidget(boton_suspender)

        if self.usuario.id == self.turno.usuario_id:
            boton_suspendidas = QPushButton("Ventas suspendidas")
            boton_suspendidas.clicked.connect(self.abrir_suspendidas)
            acciones.addWidget(boton_suspendidas)

        acciones.addStretch()
        layout.addLayout(acciones)

        layout.addWidget(self._crear_panel_inferior())
        if not self.es_dueno_turno:
            pagina.setEnabled(False)
            pagina.setToolTip(
                "Modo intervención: este turno pertenece a otro operador. "
                "No se permiten ventas ni el cierre."
            )
        QTimer.singleShot(0, self._ajustar_columnas_tabla)
        self.campo_codigo.setFocus()
        return pagina

    def eventFilter(self, objeto, evento):
        if evento.type() == QEvent.Type.KeyPress:
            tecla = evento.key()
            if objeto in (self.campo_codigo, self.campo_cantidad) and tecla in (
                Qt.Key.Key_Down,
                Qt.Key.Key_PageDown,
            ):
                if self.carrito:
                    fila = self.tabla.currentRow()
                    if fila < 0:
                        fila = len(self.carrito) - 1
                    self.tabla.setCurrentCell(fila, 0)
                    self.tabla.selectRow(fila)
                    self.tabla.setFocus()
                return True
            if objeto is self.tabla:
                if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.editar_cantidad()
                    return True
                if tecla == Qt.Key.Key_Delete:
                    self.quitar_producto()
                    return True
                if tecla == Qt.Key.Key_Escape:
                    self.campo_codigo.setFocus()
                    self.campo_codigo.selectAll()
                    return True
        return super().eventFilter(objeto, evento)

    def _registrar_pagina(self, clave, widget):
        self.paginas[clave] = widget
        self.contenedor_paginas.addWidget(widget)

    def _crear_paginas(self):
        rol = self.usuario.rol.upper()

        self._registrar_pagina(
            "caja",
            self._crear_pagina_caja(),
        )

        self._registrar_pagina(
            "productos",
            VentanaProductos(self.usuario),
        )

        if rol in ("ADMIN", "SUPERVISOR"):
            self._registrar_pagina(
                "ingreso",
                VentanaIngreso(self.usuario),
            )
            self._registrar_pagina(
                "ajuste",
                VentanaAjuste(self.usuario),
            )
            self._registrar_pagina(
                "usuarios",
                VentanaUsuarios(self.usuario),
            )
            self._registrar_pagina(
                "historial",
                VentanaHistorial(self.usuario),
            )

        if rol == "ADMIN":
            self._registrar_pagina(
                "promociones",
                VentanaPromociones(self.usuario),
            )
            self._registrar_pagina(
                "reportes_cierres",
                VentanaReportesCierres(self.usuario),
            )
            self._registrar_pagina(
                "auditoria",
                VentanaAuditoria(self.usuario),
            )
            self._registrar_pagina(
                "configuracion",
                VentanaConfiguracion(self.usuario),
            )

            if HABILITAR_DASHBOARD:
                self._registrar_pagina(
                    "dashboard",
                    VentanaDashboard(),
                )


    def _crear_navegacion(self):
        fila = QHBoxLayout()
        fila.setSpacing(5)

        self._agregar_pestana(fila, "caja", "›  Caja")

        if self.usuario.rol.upper() in ("ADMIN", "SUPERVISOR"):
            self._agregar_pestana(fila, "ingreso", "Ingreso Mercadería")
            self._agregar_pestana(fila, "ajuste", "Ajuste de Stock")

        if self.usuario.rol.upper() in ("ADMIN", "SUPERVISOR"):
            self._agregar_pestana(fila, "historial", "Historial de Ventas")

        if self.usuario.rol.upper() == "ADMIN":
            self._agregar_pestana(fila, "reportes_cierres", "Reportes de Cierres")

        if self.usuario.rol.upper() == "ADMIN":
            self._agregar_pestana(
                fila,
                "auditoria",
                "Auditoría",
            )

        if self.usuario.rol.upper() == "ADMIN" and HABILITAR_DASHBOARD:
            self._agregar_pestana(fila, "dashboard", "Dashboard")
        if self.usuario.rol.upper() == "ADMIN":
            self._agregar_pestana(fila, "promociones", "Promociones")
            
        self._agregar_pestana(fila, "productos", "Productos")

        if self.usuario.rol.upper() in ("ADMIN", "SUPERVISOR"):
            self._agregar_pestana(fila, "usuarios", "Usuarios")

        if self.usuario.rol == "ADMIN":
            self._agregar_pestana(
                fila,
                "configuracion",
                "Configuración",
            )

        fila.addStretch()
        return fila

    def _agregar_pestana(self, layout, clave, texto):
        boton = QPushButton(texto)
        boton.clicked.connect(
            lambda _checked=False, pagina=clave:
            self.mostrar_pagina(pagina)
        )
        self.botones_navegacion[clave] = boton
        layout.addWidget(boton)

    def mostrar_pagina(self, clave):
        pagina = self.paginas.get(clave)
        if pagina is None:
            return

        self.contenedor_paginas.setCurrentWidget(pagina)

        for nombre, boton in self.botones_navegacion.items():
            boton.setObjectName(
                "pestana_activa" if nombre == clave else ""
            )
            boton.style().unpolish(boton)
            boton.style().polish(boton)
            boton.update()

        if clave == "caja":
            self._actualizar_totales()
            self.campo_codigo.setFocus()
            QTimer.singleShot(0, self._ajustar_columnas_tabla)
        elif clave == "configuracion":
            pagina.refrescar()

    def _ajustar_columnas_tabla(self):
        if not hasattr(self, "tabla"):
            return

        ancho = self.tabla.viewport().width()
        if ancho <= 0:
            return

        proporciones = (0.20, 0.40, 0.10, 0.15, 0.15)
        anchos = [int(ancho * proporcion) for proporcion in proporciones]
        anchos[-1] += ancho - sum(anchos)

        for columna, ancho_columna in enumerate(anchos):
            self.tabla.setColumnWidth(columna, ancho_columna)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        QTimer.singleShot(0, self._ajustar_columnas_tabla)

    def _crear_cabecera(self):
        frame = QFrame()
        frame.setObjectName("cabecera")
        grid = QGridLayout(frame)
        grid.setContentsMargins(16, 10, 16, 10)
        grid.setHorizontalSpacing(15)

        turno = QLabel(
            f"<b>CAJA 1</b><br>"
            f"<span style='color:#0b9f4a'>{self.turno.turno.title()}</span>"
        )
        turno.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        turno.setMinimumWidth(180)
        grid.addWidget(
            turno,
            0,
            0,
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter,
        )

        titulo = QLabel("NEPOS")
        titulo.setObjectName("titulo_nepos")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setMinimumHeight(65)

        fuente = QFont()
        fuente.setFamily("Montserrat")
        fuente.setPixelSize(48)
        fuente.setWeight(QFont.Weight.Black)
        fuente.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            7,
        )

        titulo.setFont(fuente)
        grid.addWidget(
            titulo,
            0,
            1,
            Qt.AlignmentFlag.AlignCenter,
        )

        bloque_derecho = QHBoxLayout()
        bloque_derecho.setContentsMargins(0, 0, 0, 0)
        bloque_derecho.setSpacing(18)

        operador = QLabel(
            f"<b>USUARIO</b><br>{self.usuario.nombre}<br>"
            f"<span style='color:#64748b'>{self.usuario.rol.title()}</span>"
        )
        operador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bloque_derecho.addWidget(operador)

        bloque_fecha_hora = QVBoxLayout()
        bloque_fecha_hora.setContentsMargins(0, 0, 0, 0)
        bloque_fecha_hora.setSpacing(2)

        self.etiqueta_fecha = QLabel("00/00/0000")
        self.etiqueta_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_fecha.setStyleSheet(
            "font-size: 12px; color: #64748b; font-weight: 600;"
        )
        self.etiqueta_hora = QLabel("00:00")
        self.etiqueta_hora.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_hora.setStyleSheet(
            "font-size: 17px; color: #172033; font-weight: 800;"
        )

        bloque_fecha_hora.addWidget(self.etiqueta_fecha)
        bloque_fecha_hora.addWidget(self.etiqueta_hora)
        bloque_derecho.addLayout(bloque_fecha_hora)

        grid.addLayout(bloque_derecho, 0, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 1)
        return frame

    def _crear_entrada(self):
        frame = QFrame()
        frame.setObjectName("entrada")

        grid = QGridLayout(frame)
        grid.setContentsMargins(16, 10, 16, 10)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(7)

        etiqueta_codigo = QLabel("Código de barras o interno")
        etiqueta_cantidad = QLabel("Cantidad")

        grid.addWidget(etiqueta_codigo, 0, 0)
        grid.addWidget(etiqueta_cantidad, 0, 1)

        self.campo_codigo = QLineEdit()
        self.campo_codigo.setPlaceholderText(
            "Escaneá o ingresá el código"
        )
        self.campo_codigo.setMinimumHeight(48)
        self.campo_codigo.returnPressed.connect(
            self.agregar_producto
        )

        self.campo_cantidad = QLineEdit("1")
        self.campo_cantidad.setFixedWidth(130)
        self.campo_cantidad.setMinimumHeight(48)
        self.campo_cantidad.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.campo_cantidad.returnPressed.connect(
            self.agregar_producto
        )

        boton_agregar = QPushButton("AGREGAR")
        boton_agregar.setObjectName("agregar_grande")
        boton_agregar.setFixedWidth(180)
        boton_agregar.setMinimumHeight(48)
        boton_agregar.clicked.connect(
            self.agregar_producto
        )

        grid.addWidget(self.campo_codigo, 1, 0)
        grid.addWidget(self.campo_cantidad, 1, 1)
        grid.addWidget(boton_agregar, 1, 2)

        ultimo_frame = QFrame()
        ultimo_frame.setObjectName("ultimo_producto")

        fila_ultimo = QHBoxLayout(ultimo_frame)
        fila_ultimo.setContentsMargins(0, 0, 0, 0)
        fila_ultimo.setSpacing(12)

        self.etiqueta_ultimo_nombre = QLabel(
            "Esperando ingreso de producto…"
        )
        self.etiqueta_ultimo_nombre.setObjectName(
            "ultimo_nombre"
        )
        self.etiqueta_ultimo_nombre.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etiqueta_ultimo_nombre.setMinimumHeight(48)

        self.etiqueta_ultimo_precio = QLabel("$0,00")
        self.etiqueta_ultimo_precio.setObjectName(
            "ultimo_precio"
        )
        self.etiqueta_ultimo_precio.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etiqueta_ultimo_precio.setFixedWidth(220)
        self.etiqueta_ultimo_precio.setMinimumHeight(48)

        fila_ultimo.addWidget(
            self.etiqueta_ultimo_nombre,
            1,
        )
        fila_ultimo.addWidget(
            self.etiqueta_ultimo_precio,
        )

        # Ocupa todo el ancho de la sección
        grid.addWidget(ultimo_frame, 2, 0, 1, 3)

        # El campo de código utiliza todo el espacio sobrante
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 0)

        return frame

    def _crear_panel_inferior(self):
        frame = QFrame()
        frame.setObjectName("panel_inferior")
        fila = QHBoxLayout(frame)
        fila.setContentsMargins(14, 12, 14, 12)
        fila.setSpacing(18)

        bloque_total = QVBoxLayout()
        bloque_total.setSpacing(8)
        self.etiqueta_subtotal = QLabel("Subtotal: $0,00")
        self.etiqueta_descuento = QLabel("Descuentos: $0,00")
        self.etiqueta_descuento.setStyleSheet(
            "font-size:14px; color:#079447; font-weight:800;"
        )
        self.etiqueta_total = QLabel("TOTAL: $0,00")
        self.etiqueta_total.setStyleSheet(
            "font-size: 22px; color: #0a9b47; font-weight: 900;"
        )
        boton_cobrar = QPushButton("C O B R A R")
        boton_cobrar.setObjectName("primario")
        boton_cobrar.setMinimumHeight(44)
        boton_cobrar.setMinimumWidth(170)
        boton_cobrar.clicked.connect(self.cobrar)
        bloque_total.addWidget(self.etiqueta_subtotal)
        bloque_total.addWidget(self.etiqueta_descuento)
        bloque_total.addWidget(self.etiqueta_total)
        bloque_total.addStretch()
        bloque_total.addWidget(boton_cobrar)
        fila.addLayout(bloque_total, 2)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.VLine)
        separador.setStyleSheet("color: #d1d5db;")
        fila.addWidget(separador)

        bloque_turno = QVBoxLayout()
        bloque_turno.setSpacing(5)
        titulo_promociones = QLabel("PROMOCIONES APLICADAS")
        titulo_promociones.setStyleSheet(
            "font-size:13px; color:#172033; font-weight:900;"
        )
        self.etiqueta_promociones = QLabel(
            "No hay promociones aplicadas."
        )
        self.etiqueta_promociones.setWordWrap(True)
        self.etiqueta_promociones.setStyleSheet(
            "color:#64748b; font-size:12px;"
        )
        boton_cierre = QPushButton("CIERRE\nDE TURNO")
        boton_cierre.setIcon(
            QIcon(str(ruta_icono("cerrar_turno.png")))
        )
        boton_cierre.setIconSize(QSize(25, 25))
        boton_cierre.setObjectName("cierre_turno")
        boton_cierre.setFixedSize(155, 48)
        boton_cierre.clicked.connect(self.cerrar_turno)
        bloque_turno.addWidget(titulo_promociones)
        bloque_turno.addWidget(self.etiqueta_promociones, 1)
        bloque_turno.addWidget(
            boton_cierre,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        fila.addLayout(bloque_turno, 2)
        return frame

    def _iniciar_reloj(self):
        self.temporizador = QTimer(self)
        self.temporizador.timeout.connect(self._actualizar_reloj)
        self.temporizador.start(1000)
        self._actualizar_reloj()

    def _actualizar_reloj(self):
        ahora = datetime.now()
        self.etiqueta_fecha.setText(ahora.strftime("%d/%m/%Y"))
        self.etiqueta_hora.setText(ahora.strftime("%H:%M"))

    # Compatibilidad: los módulos ahora se muestran dentro de esta ventana.
    def abrir_ingreso(self):
        self.mostrar_pagina("ingreso")

    def abrir_ajuste(self):
        self.mostrar_pagina("ajuste")

    def abrir_historial(self):
        self.mostrar_pagina("historial")

    def abrir_dashboard(self):
        if not HABILITAR_DASHBOARD:
            return
        self.mostrar_pagina("dashboard")

    def abrir_usuarios(self):
        self.mostrar_pagina("usuarios")

    def abrir_productos(self):
        self.mostrar_pagina("productos")

    def abrir_configuracion(self):
        if self.usuario.rol != "ADMIN":
            return
        self.mostrar_pagina("configuracion")

    def abrir_suspendidas(self):
        if self.usuario.id != self.turno.usuario_id:
            return
        if self.carrito:
            respuesta = QMessageBox.question(
                self, "Carrito con productos",
                "Ya tenés productos cargados en la venta actual. Si recuperás una venta suspendida, "
                "se va a reemplazar lo que tenés ahora. ¿Continuar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return

        carrito_recuperado = DialogoVentasSuspendidas.elegir(
            self.turno.id,
            self.usuario.id,
            self,
        )
        if carrito_recuperado is None:
            return

        self.carrito = carrito_recuperado
        self._refrescar_tabla()

    # Carga de productos
    def buscar_por_nombre(self):
        producto = DialogoBuscarProducto.buscar(self)
        if not producto:
            return
        cantidad = self._pedir_cantidad(producto)
        if cantidad is None:
            return
        self._agregar_al_carrito(producto, cantidad)
        self._limpiar_entrada()

    def agregar_producto(self):
        codigo = self.campo_codigo.text().strip()
        if not codigo:
            return

        datos_balanza = interpretar_codigo_balanza(codigo)
        if datos_balanza:
            producto = buscar_producto_por_plu(datos_balanza["plu"])
            if not producto:
                QMessageBox.warning(
                    self,
                    "PLU no registrado",
                    f"No existe un producto con PLU '{datos_balanza['plu']}'.",
                )
                return
            self._agregar_al_carrito(
                producto,
                datos_balanza["peso_kg"],
            )
            self._limpiar_entrada()
            return

        producto = buscar_producto(codigo)
        if not producto:
            respuesta = QMessageBox.question(
                self,
                "Producto no registrado",
                "El código no existe. ¿Querés cargarlo con un precio "
                "provisorio y enviarlo a revisión de ADMIN?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
            dialogo = DialogoProductoPendiente(
                codigo,
                self.usuario,
                self,
            )
            if dialogo.exec() != QDialog.DialogCode.Accepted:
                return
            producto = dialogo.producto_creado

        if producto.pesable:
            cantidad = self._pedir_cantidad(producto)
            if cantidad is None:
                return
        else:
            try:
                cantidad = self._convertir_cantidad(
                    self.campo_cantidad.text() or "1"
                )
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Cantidad inválida",
                    "Usá un número entero válido.",
                )
                return

        try:
            validar_cantidad(
                cantidad,
                es_pesable=producto.pesable,
            )
        except ErrorVenta as error:
            QMessageBox.warning(
                self,
                "Cantidad inválida",
                str(error),
            )
            return

        self._agregar_al_carrito(producto, cantidad)
        self._limpiar_entrada()

    def _pedir_cantidad(self, producto):
        es_pesable = bool(producto.pesable)
        texto, aceptado = QInputDialog.getText(
            self,
            "Ingresar peso" if es_pesable else "Cantidad",
            (
                f"Peso en kg de {producto.descripcion}:\n"
                "Podés usar punto o coma. Ejemplo: 0,750"
                if es_pesable
                else f"Cantidad de {producto.descripcion}:"
            ),
            QLineEdit.EchoMode.Normal,
            "0,000" if es_pesable else "1",
        )
        if not aceptado:
            return None
        try:
            cantidad = self._convertir_cantidad(texto)
            validar_cantidad(
                cantidad,
                es_pesable=producto.pesable,
            )
            return cantidad
        except (ValueError, ErrorVenta) as error:
            QMessageBox.warning(
                self,
                "Cantidad inválida",
                str(error) or "Ingresá una cantidad válida.",
            )
            return None

    @staticmethod
    def _convertir_cantidad(texto):
        valor = str(texto).strip().replace(" ", "")
        if not valor:
            raise ValueError
        if "," in valor and "." in valor:
            if valor.rfind(",") > valor.rfind("."):
                valor = valor.replace(".", "").replace(",", ".")
            else:
                valor = valor.replace(",", "")
        else:
            valor = valor.replace(",", ".")
        return float(valor)

    def _permite_stock_negativo(self):
        return obtener_booleano("PERMITIR_STOCK_NEGATIVO")

    def _agregar_al_carrito(self, producto, cantidad):
        categoria = (
            producto.categoria_rel.nombre
            if producto.categoria_rel
            else ""
        )
        stock = float(producto.stock or 0)
        pendiente = bool(
            getattr(producto, "pendiente_revision", False)
        )

        for item in self.carrito:
            if item["codigo"] == producto.codigo:
                nueva_cantidad = item["cantidad"] + cantidad
                try:
                    validar_cantidad(
                        nueva_cantidad,
                        es_pesable=producto.pesable,
                    )
                except ErrorVenta as error:
                    QMessageBox.warning(
                        self,
                        "Cantidad inválida",
                        str(error),
                    )
                    return
                if (
                    not self._permite_stock_negativo()
                    and not pendiente
                    and nueva_cantidad > stock
                ):
                    self._mostrar_stock_insuficiente(producto, stock)
                    return
                item["cantidad"] = nueva_cantidad
                item["total"] = round(
                    item["precio"] * nueva_cantidad,
                    2,
                )
                item["subtotal"] = item["total"]
                self._mostrar_ultimo_producto(producto, pendiente)
                self._refrescar_tabla()
                return

        if (
            not self._permite_stock_negativo()
            and not pendiente
            and cantidad > stock
        ):
            self._mostrar_stock_insuficiente(producto, stock)
            return

        self.carrito.append(
            {
                "codigo": producto.codigo,
                "descripcion": producto.descripcion,
                "categoria": categoria,
                "cantidad": cantidad,
                "precio": float(producto.precio or 0),
                "subtotal": round(
                    float(producto.precio or 0) * cantidad,
                    2,
                ),
                "total": round(
                    float(producto.precio or 0) * cantidad,
                    2,
                ),
                "pesable": bool(producto.pesable),
                "stock_disponible": stock,
                "pendiente_revision": pendiente,
            }
        )
        self._mostrar_ultimo_producto(producto, pendiente)
        self._refrescar_tabla()

    def _mostrar_ultimo_producto(self, producto, pendiente=False):
        nombre = producto.descripcion
        if pendiente:
            nombre += " · PENDIENTE DE REVISIÓN"

        self.etiqueta_ultimo_nombre.setText(nombre.upper())
        self.etiqueta_ultimo_precio.setText(
            formatear_moneda(producto.precio or 0)
        )

    def _mostrar_stock_insuficiente(self, producto, stock):
        QMessageBox.warning(
            self,
            "Stock insuficiente",
            f"Stock disponible de {producto.descripcion}: "
            f"{formatear_cantidad(stock)}.",
        )

    def _limpiar_entrada(self):
        self.campo_codigo.clear()
        self.campo_cantidad.setText("1")
        self.campo_codigo.setFocus()


    def _fila_seleccionada(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            QMessageBox.information(
                self,
                "Elegí un producto",
                "Seleccioná una fila primero.",
            )
            return None
        return filas[0].row()

    def editar_cantidad(self, fila=None, _columna=None):
        if not isinstance(fila, int) or isinstance(fila, bool):
            fila = self._fila_seleccionada()
        if fila is None or not 0 <= fila < len(self.carrito):
            return
        item = self.carrito[fila]
        texto, aceptado = QInputDialog.getText(
            self,
            "Editar cantidad",
            f"Cantidad de {item['descripcion']}:",
            QLineEdit.EchoMode.Normal,
            formatear_cantidad(item["cantidad"]),
        )
        if not aceptado:
            return
        try:
            cantidad = self._convertir_cantidad(texto)
            validar_cantidad(
                cantidad,
                es_pesable=item["pesable"],
            )
        except (ValueError, ErrorVenta) as error:
            QMessageBox.warning(
                self,
                "Cantidad inválida",
                str(error) or "Ingresá una cantidad válida.",
            )
            return
        if (
            not self._permite_stock_negativo()
            and not item["pendiente_revision"]
            and cantidad > item["stock_disponible"]
        ):
            QMessageBox.warning(
                self,
                "Stock insuficiente",
                f"Stock disponible: "
                f"{formatear_cantidad(item['stock_disponible'])}.",
            )
            return
        item["cantidad"] = cantidad
        item["subtotal"] = round(item["precio"] * cantidad, 2)
        item["total"] = item["subtotal"]
        self._refrescar_tabla()
        self.tabla.selectRow(fila)

    def quitar_producto(self):
        fila = self._fila_seleccionada()
        if fila is None:
            return
        self.carrito.pop(fila)
        self._refrescar_tabla()
        if self.carrito:
            fila = min(fila, len(self.carrito) - 1)
            self.tabla.setCurrentCell(fila, 0)
            self.tabla.selectRow(fila)
            self.tabla.setFocus()
        else:
            self.campo_codigo.setFocus()

    def vaciar_carrito(self):
        if not self.carrito:
            return
        respuesta = QMessageBox.question(
            self,
            "Vaciar carrito",
            "¿Querés eliminar todos los productos de la venta?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self._preparar_nueva_venta()

    def suspender_venta_actual(self):
        if not self.carrito:
            QMessageBox.information(
                self, "Carrito vacío", "No hay nada para suspender."
            )
            return

        nota, _ = QInputDialog.getText(
            self, "Suspender venta", "Nota (opcional, para identificarla después):"
        )

        try:
            suspender_venta(self.turno.id, self.usuario.id, self.carrito, nota)
        except ErrorSuspendida as error:
            QMessageBox.warning(self, "No se pudo suspender", str(error))
            return

        self._preparar_nueva_venta()
        QMessageBox.information(
            self, "Venta suspendida",
            "Se guardó el carrito. Podés recuperarlo desde 'Ventas suspendidas'.",
        )

    def _refrescar_tabla(self):
        self.tabla.setRowCount(len(self.carrito))
        for fila, item in enumerate(self.carrito):
            unidad = " kg" if item["pesable"] else ""
            descripcion = item["descripcion"]
            if item.get("pendiente_revision"):
                descripcion += "  [PENDIENTE]"
            self.tabla.setItem(
                fila,
                0,
                QTableWidgetItem(item["codigo"]),
            )
            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(descripcion),
            )
            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem(
                    formatear_cantidad(item["cantidad"]) + unidad
                ),
            )
            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(formatear_moneda(item["precio"])),
            )
            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(formatear_moneda(item["total"])),
            )
        self._actualizar_totales()

    def _actualizar_totales(self):
        subtotal = round(
            sum(item["total"] for item in self.carrito),
            2,
        )
        try:
            if self.carrito:
                (
                    self.descuento_promociones,
                    self.aplicaciones_promociones,
                ) = calcular_descuento_promociones(self.carrito)
            else:
                self.descuento_promociones = 0.0
                self.aplicaciones_promociones = []
            error_promociones = None
        except Exception as error:
            self.descuento_promociones = 0.0
            self.aplicaciones_promociones = []
            error_promociones = str(error)

        total = round(
            max(subtotal - self.descuento_promociones, 0),
            2,
        )
        self.etiqueta_subtotal.setText(
            f"Subtotal: {formatear_moneda(subtotal)}"
        )
        self.etiqueta_descuento.setText(
            "Descuentos: -"
            f"{formatear_moneda(self.descuento_promociones)}"
        )
        self.etiqueta_total.setText(
            f"TOTAL: {formatear_moneda(total)}"
        )

        if error_promociones:
            self.etiqueta_promociones.setText(
                "No se pudieron calcular las promociones."
            )
            self.etiqueta_promociones.setStyleSheet(
                "color:#b42318; font-size:12px;"
            )
            self.etiqueta_promociones.setToolTip(error_promociones)
            return

        if self.aplicaciones_promociones:
            lineas = []
            for aplicacion in self.aplicaciones_promociones[:4]:
                veces = int(aplicacion.get("veces", 1))
                nombre = aplicacion.get("promocion", "Promoción")
                ahorro = aplicacion.get("ahorro", 0)
                repeticion = f" ×{veces}" if veces > 1 else ""
                lineas.append(
                    f"✓ {nombre}{repeticion}: "
                    f"-{formatear_moneda(ahorro)}"
                )
            restantes = len(self.aplicaciones_promociones) - len(lineas)
            if restantes > 0:
                lineas.append(f"… y {restantes} promoción(es) más")
            self.etiqueta_promociones.setText("\n".join(lineas))
            self.etiqueta_promociones.setStyleSheet(
                "color:#079447; font-size:12px; font-weight:700;"
            )
            self.etiqueta_promociones.setToolTip("")
        else:
            self.etiqueta_promociones.setText(
                "No hay promociones aplicadas."
            )
            self.etiqueta_promociones.setStyleSheet(
                "color:#64748b; font-size:12px;"
            )
            self.etiqueta_promociones.setToolTip("")

    def cobrar(self):
        if not self.carrito:
            QMessageBox.warning(
                self,
                "Carrito vacío",
                "Agregá al menos un producto.",
            )
            return

        dialogo = DialogoPago(self.carrito, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        pago = dialogo.resultado_pago

        try:
            resultado = registrar_venta(
                usuario_id=self.usuario.id,
                turno_id=self.turno.id,
                forma_pago=pago["forma_pago"],
                items=[
                    {
                        "codigo": item["codigo"],
                        "cantidad": item["cantidad"],
                    }
                    for item in self.carrito
                ],
                monto_efectivo=pago.get("monto_efectivo"),
                monto_qr=pago.get("monto_qr"),
                monto_debito=pago.get("monto_debito"),
                monto_credito=pago.get("monto_credito"),
                monto_recibido=pago.get("monto_recibido"),
                cigarrillos_en_efectivo=pago.get(
                    "cigarrillos_en_efectivo",
                    False,
                ),
                cuotas=pago.get("cuotas"),
            )
        except ErrorVenta as error:
            QMessageBox.critical(
                self,
                "No se pudo cobrar",
                str(error),
            )
            return
        except TypeError:
            QMessageBox.critical(
                self,
                "Archivos incompatibles",
                "Actualizá también services/venta_service.py para usar "
                "el pago combinado nuevo.",
            )
            return

        mensaje = (
            f"Venta N° {resultado['numero']} guardada.\n"
            f"Total: {formatear_moneda(resultado['total'])}"
        )
        if resultado.get("recargo", 0):
            mensaje += (
                f"\nRecargos: "
                f"{formatear_moneda(resultado['recargo'])}"
            )
        if resultado.get("descuento_promociones", 0):
            mensaje += (
                f"\nPromociones: -"
                f"{formatear_moneda(resultado['descuento_promociones'])}"
            )
        if resultado.get("vuelto", 0):
            mensaje += (
                f"\nVuelto: "
                f"{formatear_moneda(resultado['vuelto'])}"
            )

        if pago.get("imprimir_ticket", True):
            try:
                imprimir_ticket_venta(
                    resultado=resultado,
                    carrito=self.carrito,
                    usuario=self.usuario,
                    turno=self.turno,
                    pago=pago,
                )
                mensaje += "\n\nTicket enviado a la impresora configurada."
            except ErrorImpresion as error:
                mensaje += (
                    "\n\nLa venta quedó guardada, pero no se pudo imprimir "
                    f"el ticket:\n{error}"
                )
        else:
            mensaje += "\n\nVenta registrada sin imprimir ticket."
        QMessageBox.information(
            self,
            "Venta registrada",
            mensaje,
        )
        self._preparar_nueva_venta()

    def _preparar_nueva_venta(self):
        self.carrito = []
        self.etiqueta_ultimo_nombre.setText(
            "Esperando ingreso de producto…"
        )
        self.etiqueta_ultimo_precio.setText("$0,00")
        self._limpiar_entrada()
        self._refrescar_tabla()

    
    def cerrar_turno(self):
        resumen = calcular_resumen(self.turno.id)
        efectivo_texto, aceptado = QInputDialog.getText(
            self,
            "Arqueo de caja",
            "Contá el dinero de la caja e ingresá el efectivo total:\n"
            "(incluye el fondo inicial)",
        )
        if not aceptado:
            return
        try:
            efectivo_declarado = convertir_decimal_finito(
                efectivo_texto,
                nombre="El efectivo contado",
                minimo=0,
                maximo=100000000,
                interpretar_punto_miles=True,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Importe inválido", str(error))
            return

        diferencia = round(
            efectivo_declarado - resumen["efectivo_esperado_en_caja"],
            2,
        )
        observacion = ""
        if abs(diferencia) >= 0.01:
            estado = "SOBRANTE" if diferencia > 0 else "FALTANTE"
            observacion, aceptado = QInputDialog.getText(
                self,
                f"Caja con {estado.lower()}",
                f"Diferencia: {formatear_moneda(diferencia)} · {estado}\n"
                "Ingresá una observación obligatoria:",
            )
            if not aceptado:
                return
            if not observacion.strip():
                QMessageBox.warning(
                    self,
                    "Observación obligatoria",
                    "Debés explicar el sobrante o faltante antes de cerrar.",
                )
                return

        estado_caja = (
            "OK"
            if abs(diferencia) < 0.01
            else ("SOBRANTE" if diferencia > 0 else "FALTANTE")
        )
        texto = (
            f"Turno: {resumen['turno']}\n"
            f"Cajero: {resumen['cajero']}\n\n"
            f"Transacciones: {resumen['transacciones']}\n"
            f"Unidades vendidas: "
            f"{formatear_cantidad(resumen['unidades'])}\n"
            f"Pesables vendidos (kg): "
            f"{formatear_cantidad(resumen['pesables'])}\n\n"
            f"Venta bruta: "
            f"{formatear_moneda(resumen['venta_bruta'])}\n"
            f"Recargos: "
            f"{formatear_moneda(resumen['recargos'])}\n\n"
            f"IVA 10,5% incluido: "
            f"{formatear_moneda(resumen['iva_10_5'])}\n"
            f"IVA 21% incluido: "
            f"{formatear_moneda(resumen['iva_21'])}\n\n"
            f"Efectivo: {formatear_moneda(resumen['efectivo'])}\n"
            f"QR: {formatear_moneda(resumen['qr'])}\n"
            f"Débito: {formatear_moneda(resumen['debito'])}\n"
            f"Crédito: {formatear_moneda(resumen['credito'])}\n\n"
            f"Fondo inicial: "
            f"{formatear_moneda(resumen['fondo_inicial'])}\n"
            f"Efectivo esperado: "
            f"{formatear_moneda(resumen['efectivo_esperado_en_caja'])}\n"
            f"Efectivo contado: {formatear_moneda(efectivo_declarado)}\n"
            f"Diferencia: {formatear_moneda(diferencia)} · {estado_caja}"
            "\n\n¿Confirmás el cierre?"
        )
        respuesta = QMessageBox.question(
            self,
            "Cierre de turno",
            texto,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            cerrar_turno(
                self.turno.id,
                self.usuario.id,
                efectivo_declarado=efectivo_declarado,
                observacion_cierre=observacion,
            )
        except ErrorCierre as error:
            QMessageBox.critical(
                self,
                "No se pudo cerrar",
                str(error),
            )
            return
        resumen = calcular_resumen(self.turno.id)
        carpeta_cierres = directorio_cierres()
        nombre_base = f"cierre_turno_{self.turno.id}_{date.today().isoformat()}"
        ruta_excel = str(carpeta_cierres / f"{nombre_base}.xlsx")
        ruta_pdf = str(carpeta_cierres / f"{nombre_base}.pdf")

        try:
            exportar_cierre_turno_excel(resumen, ruta_excel)
            exportar_cierre_turno_pdf(resumen, ruta_pdf)
            mensaje_archivos = (
                f"\n\nArchivos generados en:\n{carpeta_cierres}\n"
                f"{nombre_base}.xlsx\n{nombre_base}.pdf"
            )
        except Exception as error:
            mensaje_archivos = f"\n\n(No se pudieron generar los archivos: {error})"

        try:
            ruta_backup = hacer_backup()
            mensaje_archivos += f"\n\nBackup de cierre creado:\n{ruta_backup}"
        except Exception as error:
            mensaje_archivos += (
                "\n\nADVERTENCIA: el turno se cerró, pero falló el backup: "
                f"{error}"
            )

        QMessageBox.information(
            self,
            "Turno cerrado",
            "El turno se cerró correctamente." + mensaje_archivos,
        )
        self.close()
        if self.al_cerrar_turno:
            self.al_cerrar_turno()