from utils.rutas import ruta_icono

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.promocion_service import (
    ErrorPromocion,
    TIPOS_PROMOCION,
    desactivar_promocion,
    guardar_promocion,
    listar_opciones_promocion,
    listar_promociones,
)
from ui.estilos import ESTILO_GLOBAL
from utils.formato import formatear_moneda


ROL_ORDEN = int(Qt.ItemDataRole.UserRole)
ROL_PROMOCION_ID = ROL_ORDEN + 1


class ItemOrdenable(QTableWidgetItem):
    def __init__(self, texto, valor_orden=None):
        super().__init__(str(texto))
        self.setData(
            ROL_ORDEN,
            valor_orden if valor_orden is not None else str(texto),
        )

    def __lt__(self, otro):
        propio = self.data(ROL_ORDEN)
        ajeno = otro.data(ROL_ORDEN)
        try:
            return propio < ajeno
        except TypeError:
            return str(propio).casefold() < str(ajeno).casefold()


class ComboBusqueda(QComboBox):
    """Combo editable que abre coincidencias mientras se escribe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lineEdit().setClearButtonEnabled(True)
        self.lineEdit().textEdited.connect(self._mostrar_coincidencias)

    def establecer_placeholder(self, texto):
        self.lineEdit().setPlaceholderText(texto)

    def configurar_completer(self):
        completador = self.completer()
        if completador is None:
            return
        completador.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completador.setFilterMode(Qt.MatchFlag.MatchContains)
        completador.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completador.setMaxVisibleItems(12)

    def _mostrar_coincidencias(self, texto):
        texto = texto.strip()
        if not texto:
            return
        completador = self.completer()
        if completador is not None:
            completador.setCompletionPrefix(texto)
            completador.complete()

    def focusInEvent(self, evento):
        super().focusInEvent(evento)
        if self.currentIndex() < 0:
            self.lineEdit().clear()
        else:
            self.lineEdit().selectAll()


class TablaConScrollGeneral(QTableWidget):
    """Al llegar al borde de la tabla continúa desplazando la página."""

    def wheelEvent(self, evento):
        barra = self.verticalScrollBar()
        delta = evento.angleDelta().y()
        puede_subir = barra.value() > barra.minimum()
        puede_bajar = barra.value() < barra.maximum()

        if (delta > 0 and puede_subir) or (delta < 0 and puede_bajar):
            super().wheelEvent(evento)
            return

        padre = self.parent()
        while padre is not None:
            if (
                isinstance(padre, QScrollArea)
                and padre.objectName() == "scroll_principal_promociones"
            ):
                barra_pagina = padre.verticalScrollBar()
                movimiento = int(
                    (delta / 120) * barra_pagina.singleStep() * 4
                )
                barra_pagina.setValue(barra_pagina.value() - movimiento)
                evento.accept()
                return
            padre = padre.parent()

        super().wheelEvent(evento)


class VentanaPromociones(QWidget):
    CANTIDAD_SLOTS_INICIALES = 4
    CANTIDAD_SLOTS_MAXIMA = 20

    def __init__(self, usuario):
        super().__init__()
        self.usuario = usuario
        self.promocion_editada_id = None
        self._promociones_cargadas = []
        self._promociones_por_id = {}
        self._opciones = {"productos": [], "grupos": []}

        self.setWindowTitle("NEPOS — Promociones")
        self.setStyleSheet(ESTILO_GLOBAL)
        self._armar_interfaz()
        self._cargar_opciones()
        self._refrescar_tabla()
        self._cambiar_tipo()

    # ---------------------------------------------------------
    # Interfaz
    # ---------------------------------------------------------
    def _armar_interfaz(self):
        exterior = QVBoxLayout(self)
        exterior.setContentsMargins(0, 0, 0, 0)
        exterior.setSpacing(0)

        self.scroll_principal = QScrollArea()
        self.scroll_principal.setObjectName("scroll_principal_promociones")
        self.scroll_principal.setWidgetResizable(True)
        self.scroll_principal.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_principal.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_principal.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        contenido = QWidget()
        contenido.setObjectName("contenido_promociones")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(18, 12, 18, 16)
        layout.setSpacing(10)
        layout.addWidget(self._crear_cabecera())
        layout.addWidget(self._crear_formulario())

        tabla_frame = self._crear_tabla_promociones()
        tabla_frame.setMinimumHeight(365)
        layout.addWidget(tabla_frame)

        self.scroll_principal.setWidget(contenido)
        exterior.addWidget(self.scroll_principal)
        QTimer.singleShot(0, self._ajustar_columnas_tabla)

    def _crear_cabecera(self):
        cabecera = QFrame()
        cabecera.setObjectName("tarjeta")
        fila = QHBoxLayout(cabecera)
        fila.setContentsMargins(18, 10, 18, 10)
        fila.setSpacing(11)

        icono = QLabel()
        pixmap = QPixmap(str(ruta_icono("promociones.png")))
        if pixmap.isNull():
            icono.setText("◆")
            icono.setStyleSheet("font-size:25px; color:#887bd4;")
        else:
            icono.setPixmap(
                pixmap.scaled(
                    34,
                    34,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        icono.setFixedSize(40, 40)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        textos = QVBoxLayout()
        textos.setContentsMargins(0, 0, 0, 0)
        textos.setSpacing(1)
        titulo = QLabel("PROMOCIONES")
        titulo.setObjectName("titulo_modulo")
        subtitulo = QLabel(
            "Creá reglas por producto o grupo y aplicalas automáticamente "
            "durante la venta."
        )
        subtitulo.setObjectName("subtitulo")
        textos.addWidget(titulo)
        textos.addWidget(subtitulo)

        fila.addWidget(icono)
        fila.addLayout(textos)
        fila.addStretch()
        return cabecera

    def _crear_boton_opcion(self, texto, seleccionada=False):
        boton = QPushButton()
        boton.setObjectName("opcion_promocion")
        boton.setCheckable(True)
        boton.setChecked(seleccionada)
        boton.setMinimumHeight(40)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)

        def actualizar(estado):
            boton.setText(f"{'✓' if estado else '○'}  {texto}")

        boton.toggled.connect(actualizar)
        actualizar(seleccionada)
        return boton

    def _crear_formulario(self):
        formulario = QFrame()
        formulario.setObjectName("tarjeta")
        grid = QGridLayout(formulario)
        grid.setContentsMargins(14, 11, 14, 11)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        for columna in range(4):
            grid.setColumnStretch(columna, 1)

        grid.addWidget(QLabel("Nombre de la promoción"), 0, 0)
        grid.addWidget(QLabel("Tipo de promoción"), 0, 2)
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText(
            "Ej.: 2x1 Manaos 3L, Segunda Coca al 50%..."
        )
        self.campo_nombre.setMinimumHeight(42)
        self.combo_tipo = QComboBox()
        self.combo_tipo.setMinimumHeight(42)
        for clave, nombre in TIPOS_PROMOCION.items():
            self.combo_tipo.addItem(nombre, clave)
        self.combo_tipo.currentIndexChanged.connect(self._cambiar_tipo)
        grid.addWidget(self.campo_nombre, 1, 0, 1, 2)
        grid.addWidget(self.combo_tipo, 1, 2, 1, 2)

        self.campos_regla = {}
        fila_parametros = QHBoxLayout()
        fila_parametros.setSpacing(8)
        definiciones = [
            ("cantidad_lleva", "Cantidad que lleva", "2"),
            ("cantidad_paga", "Cantidad que paga", "1"),
            ("porcentaje", "Descuento (%)", "15"),
            ("porcentaje_maximo", "Descuento máximo (%)", "50"),
            ("cantidad_minima", "Cantidad mínima", "1"),
            ("precio_promocional", "Precio final", ""),
            ("descuento_fijo", "Descuento fijo", ""),
        ]
        for clave, texto, defecto in definiciones:
            contenedor = QWidget()
            columna = QVBoxLayout(contenedor)
            columna.setContentsMargins(0, 0, 0, 0)
            columna.setSpacing(2)
            etiqueta = QLabel(texto)
            campo = QLineEdit(defecto)
            campo.setMinimumHeight(40)
            columna.addWidget(etiqueta)
            columna.addWidget(campo)
            fila_parametros.addWidget(contenedor, 1)
            self.campos_regla[clave] = (contenedor, campo)
        grid.addLayout(fila_parametros, 2, 0, 1, 4)

        opciones = QHBoxLayout()
        opciones.setSpacing(9)
        self.check_repetible = self._crear_boton_opcion(
            "Repetible según la cantidad", True
        )
        self.check_repetible.setMinimumWidth(245)
        self.check_acumulable = self._crear_boton_opcion(
            "Acumulable con otras promociones", False
        )
        self.check_acumulable.setMinimumWidth(285)
        self.combo_prioridad = QComboBox()
        self.combo_prioridad.addItem("Alta — aplicar primero", 10)
        self.combo_prioridad.addItem("Media — orden normal", 100)
        self.combo_prioridad.addItem("Baja — aplicar al final", 200)
        self.combo_prioridad.setCurrentIndex(1)
        self.combo_prioridad.setFixedWidth(260)
        self.combo_prioridad.setMinimumHeight(40)
        etiqueta_prioridad = QLabel("Prioridad:")
        etiqueta_prioridad.setObjectName("etiqueta_prioridad_promocion")
        opciones.addWidget(self.check_repetible)
        opciones.addWidget(self.check_acumulable)
        opciones.addSpacing(6)
        opciones.addWidget(etiqueta_prioridad)
        opciones.addWidget(self.combo_prioridad)
        opciones.addStretch()
        grid.addLayout(opciones, 3, 0, 1, 4)

        cabecera_alcance = QVBoxLayout()
        cabecera_alcance.setSpacing(1)
        titulo_alcance = QLabel("PRODUCTOS O GRUPOS ALCANZADOS")
        titulo_alcance.setObjectName("titulo_alcance_promocion")
        ayuda = QLabel(
            "En combos, cada fila es obligatoria. En los demás tipos, "
            "las filas representan artículos elegibles."
        )
        ayuda.setObjectName("subtitulo")
        cabecera_alcance.addWidget(titulo_alcance)
        cabecera_alcance.addWidget(ayuda)
        grid.addLayout(cabecera_alcance, 4, 0, 1, 4)

        self.filas_alcance = []
        self.contenedor_alcances = QWidget()
        self.contenedor_alcances.setObjectName("contenedor_alcances_promocion")
        self.contenedor_alcances.setMaximumWidth(1050)
        self.grilla_alcances = QGridLayout(self.contenedor_alcances)
        self.grilla_alcances.setContentsMargins(0, 0, 0, 0)
        self.grilla_alcances.setVerticalSpacing(6)
        self.grilla_alcances.setColumnStretch(0, 1)
        fila_alcances = QHBoxLayout()
        fila_alcances.setContentsMargins(0, 0, 0, 0)
        fila_alcances.addWidget(
            self.contenedor_alcances,
            0,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
        )
        fila_alcances.addStretch()
        grid.addLayout(fila_alcances, 5, 0, 1, 4)

        acciones = QWidget()
        acciones.setObjectName("contenedor_acciones_promocion")
        acciones.setMaximumWidth(1050)
        barra = QHBoxLayout(acciones)
        barra.setContentsMargins(0, 5, 0, 0)
        barra.setSpacing(9)

        self.boton_agregar_alcance = QPushButton(
            "＋  Agregar producto o grupo"
        )
        self.boton_agregar_alcance.setObjectName("agregar_alcance_promocion")
        self.boton_agregar_alcance.setFixedSize(255, 42)
        self.boton_agregar_alcance.clicked.connect(self._agregar_fila_alcance)
        self.boton_nueva = QPushButton("Nueva / limpiar")
        self.boton_nueva.setObjectName("nueva_promocion")
        self.boton_nueva.setFixedSize(155, 42)
        self.boton_nueva.clicked.connect(self._limpiar_formulario)
        self.boton_guardar = QPushButton("✓  Crear promoción")
        self.boton_guardar.setObjectName("guardar_promocion")
        self.boton_guardar.setFixedSize(205, 42)
        self.boton_guardar.clicked.connect(self.guardar)
        for boton in (
            self.boton_agregar_alcance,
            self.boton_nueva,
            self.boton_guardar,
        ):
            boton.setCursor(Qt.CursorShape.PointingHandCursor)

        barra.addWidget(self.boton_agregar_alcance)
        barra.addStretch()
        barra.addWidget(self.boton_nueva)
        barra.addWidget(self.boton_guardar)
        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.addWidget(acciones, 0, Qt.AlignmentFlag.AlignLeft)
        fila_acciones.addStretch()
        grid.addLayout(fila_acciones, 6, 0, 1, 4)

        for _ in range(self.CANTIDAD_SLOTS_INICIALES):
            self._agregar_fila_alcance()
        return formulario

    def _crear_tabla_promociones(self):
        frame = QFrame()
        frame.setObjectName("tarjeta")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(7, 7, 7, 7)
        layout.setSpacing(6)

        titulo = QLabel("PROMOCIONES EXISTENTES")
        titulo.setObjectName("titulo_tabla_promociones")
        layout.addWidget(titulo)
        self.tabla = TablaConScrollGeneral(0, 6)
        self.tabla.setMinimumHeight(285)
        self.tabla.setHorizontalHeaderLabels(
            ["NOMBRE", "TIPO", "ALCANCE", "BENEFICIO", "PRIORIDAD", "ESTADO"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(35)
        encabezado = self.tabla.horizontalHeader()
        encabezado.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        encabezado.setSectionsClickable(True)
        encabezado.setSortIndicatorShown(True)
        self.tabla.setSortingEnabled(True)
        self.tabla.cellDoubleClicked.connect(self._editar_fila)
        self.tabla.itemSelectionChanged.connect(self._actualizar_botones_tabla)
        layout.addWidget(self.tabla, 1)

        inferior = QHBoxLayout()
        ayuda = QLabel("Seleccioná una promoción o hacé doble clic para editarla.")
        ayuda.setObjectName("subtitulo")
        inferior.addWidget(ayuda)
        inferior.addStretch()
        self.boton_editar = QPushButton("Editar seleccionada")
        self.boton_editar.setObjectName("editar_promocion")
        self.boton_editar.setEnabled(False)
        self.boton_editar.clicked.connect(self._editar_seleccionada)
        self.boton_alternar = QPushButton("Activar / desactivar")
        self.boton_alternar.setObjectName("alternar_promocion")
        self.boton_alternar.setEnabled(False)
        self.boton_alternar.clicked.connect(self.alternar)
        inferior.addWidget(self.boton_editar)
        inferior.addWidget(self.boton_alternar)
        layout.addLayout(inferior)
        return frame

    # ---------------------------------------------------------
    # Alcances
    # ---------------------------------------------------------
    def _cargar_opciones(self):
        self._opciones = listar_opciones_promocion()
        for fila in self.filas_alcance:
            self._cargar_objetivos(fila["alcance"], fila["objetivo"])

    def _agregar_fila_alcance(self, _checked=False):
        if len(self.filas_alcance) >= self.CANTIDAD_SLOTS_MAXIMA:
            QMessageBox.information(
                self,
                "Límite alcanzado",
                f"Se permiten hasta {self.CANTIDAD_SLOTS_MAXIMA} "
                "productos o grupos por promoción.",
            )
            return None

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta_alcance_promocion")
        tarjeta.setMaximumWidth(1000)
        tarjeta.setMinimumHeight(52)
        contenido = QHBoxLayout(tarjeta)
        contenido.setContentsMargins(7, 5, 7, 5)
        contenido.setSpacing(7)

        numero = QLabel()
        numero.setFixedWidth(28)
        numero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        numero.setStyleSheet("font-weight:800;")
        alcance = QComboBox()
        alcance.addItem("Producto", "PRODUCTO")
        alcance.addItem("Grupo", "GRUPO")
        alcance.setFixedWidth(125)
        objetivo = ComboBusqueda()
        objetivo.setMinimumWidth(420)
        etiqueta_cantidad = QLabel("Cantidad:")
        cantidad = QLineEdit("1")
        cantidad.setFixedWidth(70)
        boton_quitar = QPushButton("×")
        boton_quitar.setObjectName("quitar_alcance_promocion")
        boton_quitar.setToolTip("Quitar este producto o grupo")
        boton_quitar.setFixedSize(34, 34)

        contenido.addWidget(numero)
        contenido.addWidget(alcance)
        contenido.addWidget(objetivo, 1)
        contenido.addWidget(etiqueta_cantidad)
        contenido.addWidget(cantidad)
        contenido.addWidget(boton_quitar)
        fila = {
            "tarjeta": tarjeta,
            "numero": numero,
            "alcance": alcance,
            "objetivo": objetivo,
            "cantidad": cantidad,
            "etiqueta_cantidad": etiqueta_cantidad,
        }
        alcance.currentIndexChanged.connect(
            lambda _indice, a=alcance, o=objetivo: self._cargar_objetivos(
                a, o, conservar=False
            )
        )
        boton_quitar.clicked.connect(
            lambda _checked=False, actual=fila: self._quitar_fila_alcance(actual)
        )
        self.filas_alcance.append(fila)
        self._cargar_objetivos(alcance, objetivo)
        self._reordenar_filas_alcance()
        self._actualizar_cantidades_componentes()
        return fila

    def _quitar_fila_alcance(self, fila):
        if fila not in self.filas_alcance:
            return
        if len(self.filas_alcance) == 1:
            fila["objetivo"].setCurrentIndex(-1)
            fila["objetivo"].lineEdit().clear()
            fila["cantidad"].setText("1")
            return
        self.filas_alcance.remove(fila)
        self.grilla_alcances.removeWidget(fila["tarjeta"])
        fila["tarjeta"].deleteLater()
        self._reordenar_filas_alcance()

    def _reordenar_filas_alcance(self):
        for indice, fila in enumerate(self.filas_alcance):
            self.grilla_alcances.removeWidget(fila["tarjeta"])
            fila["numero"].setText(f"{indice + 1}.")
            self.grilla_alcances.addWidget(
                fila["tarjeta"], indice, 0, Qt.AlignmentFlag.AlignTop
            )

    def _actualizar_cantidades_componentes(self):
        mostrar = self.combo_tipo.currentData() == "COMBO_PRECIO"
        for fila in self.filas_alcance:
            fila["cantidad"].setVisible(mostrar)
            fila["etiqueta_cantidad"].setVisible(mostrar)

    def _cargar_objetivos(self, alcance, objetivo, conservar=True):
        seleccion = objetivo.currentData() if conservar else None
        objetivo.blockSignals(True)
        objetivo.clear()
        if alcance.currentData() == "PRODUCTO":
            objetivo.establecer_placeholder(
                "Buscar por código o nombre del producto…"
            )
            for producto in self._opciones["productos"]:
                objetivo.addItem(
                    f"{producto['codigo']} · {producto['descripcion']}",
                    producto["id"],
                )
        else:
            objetivo.establecer_placeholder("Buscar por nombre del grupo…")
            for grupo in self._opciones["grupos"]:
                objetivo.addItem(grupo["nombre"], grupo["id"])
        indice = objetivo.findData(seleccion)
        objetivo.setCurrentIndex(indice if indice >= 0 else -1)
        if indice < 0:
            objetivo.lineEdit().clear()
        objetivo.configurar_completer()
        objetivo.blockSignals(False)

    # ---------------------------------------------------------
    # Reglas y guardado
    # ---------------------------------------------------------
    def _cambiar_tipo(self, _indice=None):
        tipo = self.combo_tipo.currentData()
        visibles = {
            "NXM": {"cantidad_lleva", "cantidad_paga"},
            "PORCENTAJE": {"porcentaje", "cantidad_minima"},
            "PRECIO_CANTIDAD": {"cantidad_lleva", "precio_promocional"},
            "COMBO_PRECIO": {"precio_promocional"},
            "SEGUNDA_UNIDAD": {"porcentaje"},
            "PORCENTAJE_ESCALONADO": {
                "cantidad_lleva",
                "porcentaje",
                "porcentaje_maximo",
            },
            "DESCUENTO_FIJO": {"cantidad_minima", "descuento_fijo"},
        }.get(tipo, set())
        for clave, (contenedor, campo) in self.campos_regla.items():
            visible = clave in visibles
            contenedor.setVisible(visible)
            campo.setVisible(visible)
        self._actualizar_cantidades_componentes()

    @staticmethod
    def _valor(campo):
        texto = campo.text().strip().replace(" ", "")
        if not texto:
            return None
        if "," in texto and "." in texto:
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")
        elif "," in texto:
            texto = texto.replace(",", ".")
        return float(texto)

    def _items_formulario(self):
        items = []
        es_combo = self.combo_tipo.currentData() == "COMBO_PRECIO"
        for fila in self.filas_alcance:
            identificador = fila["objetivo"].currentData()
            if identificador is None:
                continue
            cantidad = self._valor(fila["cantidad"]) if es_combo else 1
            if cantidad is None or cantidad <= 0:
                raise ErrorPromocion(
                    "La cantidad de cada componente debe ser mayor que cero."
                )
            es_producto = fila["alcance"].currentData() == "PRODUCTO"
            items.append(
                {
                    "producto_id": identificador if es_producto else None,
                    "grupo_precio_id": None if es_producto else identificador,
                    "cantidad": cantidad,
                }
            )
        return items

    def guardar(self):
        try:
            valores = {
                clave: self._valor(campo)
                for clave, (_contenedor, campo) in self.campos_regla.items()
            }
            identificador = guardar_promocion(
                promocion_id=self.promocion_editada_id,
                nombre=self.campo_nombre.text(),
                tipo=self.combo_tipo.currentData(),
                items=self._items_formulario(),
                usuario_id=self.usuario.id,
                repetible=self.check_repetible.isChecked(),
                acumulable=self.check_acumulable.isChecked(),
                prioridad=self.combo_prioridad.currentData(),
                **valores,
            )
        except (ErrorPromocion, TypeError, ValueError) as error:
            QMessageBox.warning(self, "Revisá la promoción", str(error))
            return
        QMessageBox.information(
            self,
            "Promoción guardada",
            f"La promoción N.º {identificador} se guardó correctamente.",
        )
        self._limpiar_formulario()
        self._refrescar_tabla()

    # ---------------------------------------------------------
    # Tabla, selección y edición
    # ---------------------------------------------------------
    def _alcance_texto(self, promocion):
        valores = []
        for item in promocion.items:
            if item.producto:
                valores.append(item.producto.descripcion)
            elif item.grupo_precio:
                valores.append(f"Grupo: {item.grupo_precio.nombre}")
        return " + ".join(valores)

    @staticmethod
    def _beneficio_texto(promocion):
        tipo = promocion.tipo
        if tipo == "NXM":
            return f"{promocion.cantidad_lleva:g}x{promocion.cantidad_paga:g}"
        if tipo == "PORCENTAJE":
            return f"{promocion.porcentaje:g}%"
        if tipo in ("PRECIO_CANTIDAD", "COMBO_PRECIO"):
            return formatear_moneda(promocion.precio_promocional or 0)
        if tipo == "SEGUNDA_UNIDAD":
            return f"2.ª unidad: {promocion.porcentaje:g}%"
        if tipo == "PORCENTAJE_ESCALONADO":
            return (
                f"{promocion.porcentaje:g}% cada {promocion.cantidad_lleva:g} "
                f"(máx. {promocion.porcentaje_maximo:g}%)"
            )
        if tipo == "DESCUENTO_FIJO":
            return formatear_moneda(promocion.descuento_fijo or 0)
        return "—"

    @staticmethod
    def _beneficio_orden(promocion):
        if promocion.tipo == "NXM":
            return float(promocion.cantidad_lleva or 0)
        if promocion.tipo in (
            "PORCENTAJE",
            "SEGUNDA_UNIDAD",
            "PORCENTAJE_ESCALONADO",
        ):
            return float(promocion.porcentaje or 0)
        if promocion.tipo in ("PRECIO_CANTIDAD", "COMBO_PRECIO"):
            return float(promocion.precio_promocional or 0)
        if promocion.tipo == "DESCUENTO_FIJO":
            return float(promocion.descuento_fijo or 0)
        return 0

    @staticmethod
    def _prioridad_texto(valor):
        prioridad = int(valor or 100)
        if prioridad <= 50:
            return "Alta"
        if prioridad <= 150:
            return "Media"
        return "Baja"

    def _refrescar_tabla(self):
        promociones = listar_promociones()
        self._promociones_cargadas = promociones
        self._promociones_por_id = {p.id: p for p in promociones}
        ordenar = self.tabla.isSortingEnabled()
        self.tabla.setSortingEnabled(False)
        self.tabla.clearContents()
        self.tabla.setRowCount(len(promociones))

        for fila, promocion in enumerate(promociones):
            prioridad = int(promocion.prioridad or 100)
            activa = bool(promocion.activa)
            alcance = self._alcance_texto(promocion)
            tipo = TIPOS_PROMOCION.get(promocion.tipo, promocion.tipo)
            textos = [
                promocion.nombre,
                tipo,
                alcance,
                self._beneficio_texto(promocion),
                self._prioridad_texto(prioridad),
                "Activa" if activa else "Inactiva",
            ]
            orden = [
                promocion.nombre.casefold(),
                tipo.casefold(),
                alcance.casefold(),
                self._beneficio_orden(promocion),
                prioridad,
                0 if activa else 1,
            ]
            for columna, texto in enumerate(textos):
                item = ItemOrdenable(texto, orden[columna])
                item.setData(ROL_PROMOCION_ID, promocion.id)
                if columna == 5:
                    item.setForeground(QColor("#15803d" if activa else "#b91c1c"))
                self.tabla.setItem(fila, columna, item)

        self.tabla.setSortingEnabled(ordenar)
        self.tabla.clearSelection()
        self._actualizar_botones_tabla()
        QTimer.singleShot(0, self._ajustar_columnas_tabla)

    def _promocion_en_fila(self, fila):
        item = self.tabla.item(fila, 0) if fila >= 0 else None
        if item is None:
            return None
        return self._promociones_por_id.get(item.data(ROL_PROMOCION_ID))

    def _promocion_seleccionada(self, mostrar_aviso=True):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas:
            if mostrar_aviso:
                QMessageBox.information(
                    self,
                    "Elegí una promoción",
                    "Seleccioná una promoción de la lista.",
                )
            return None
        return self._promocion_en_fila(filas[0].row())

    def _actualizar_botones_tabla(self):
        promocion = self._promocion_seleccionada(False)
        habilitar = promocion is not None
        self.boton_editar.setEnabled(habilitar)
        self.boton_alternar.setEnabled(habilitar)
        if promocion is None:
            texto, objeto = "Activar / desactivar", "alternar_promocion"
        elif promocion.activa:
            texto, objeto = "Desactivar promoción", "desactivar_promocion"
        else:
            texto, objeto = "Activar promoción", "activar_promocion"
        self.boton_alternar.setText(texto)
        self.boton_alternar.setObjectName(objeto)
        self.boton_alternar.style().unpolish(self.boton_alternar)
        self.boton_alternar.style().polish(self.boton_alternar)

    def _editar_seleccionada(self):
        promocion = self._promocion_seleccionada()
        if promocion is not None:
            self._cargar_promocion(promocion)

    def _editar_fila(self, fila, _columna):
        promocion = self._promocion_en_fila(fila)
        if promocion is not None:
            self._cargar_promocion(promocion)

    @staticmethod
    def _texto_numero(valor):
        return "" if valor is None else f"{float(valor):g}".replace(".", ",")

    def _seleccionar_prioridad(self, valor):
        prioridad = int(valor or 100)
        valor_combo = 10 if prioridad <= 50 else 100 if prioridad <= 150 else 200
        indice = self.combo_prioridad.findData(valor_combo)
        self.combo_prioridad.setCurrentIndex(indice if indice >= 0 else 1)

    def _cargar_promocion(self, promocion):
        self.promocion_editada_id = promocion.id
        self.campo_nombre.setText(promocion.nombre)
        indice = self.combo_tipo.findData(promocion.tipo)
        self.combo_tipo.setCurrentIndex(max(indice, 0))
        for clave, (_contenedor, campo) in self.campos_regla.items():
            campo.setText(self._texto_numero(getattr(promocion, clave, None)))
        self.check_repetible.setChecked(bool(promocion.repetible))
        self.check_acumulable.setChecked(bool(promocion.acumulable))
        self._seleccionar_prioridad(promocion.prioridad)

        cantidad_items = min(len(promocion.items), self.CANTIDAD_SLOTS_MAXIMA)
        filas_necesarias = max(self.CANTIDAD_SLOTS_INICIALES, cantidad_items)
        while len(self.filas_alcance) < filas_necesarias:
            self._agregar_fila_alcance()
        while len(self.filas_alcance) > filas_necesarias:
            self._quitar_fila_alcance(self.filas_alcance[-1])
        for fila in self.filas_alcance:
            fila["objetivo"].setCurrentIndex(-1)
            fila["objetivo"].lineEdit().clear()
            fila["cantidad"].setText("1")

        for fila, item in zip(
            self.filas_alcance, promocion.items[:cantidad_items]
        ):
            alcance = fila["alcance"]
            alcance.blockSignals(True)
            alcance.setCurrentIndex(
                alcance.findData("PRODUCTO" if item.producto_id else "GRUPO")
            )
            alcance.blockSignals(False)
            self._cargar_objetivos(alcance, fila["objetivo"], conservar=False)
            identificador = item.producto_id or item.grupo_precio_id
            fila["objetivo"].setCurrentIndex(
                fila["objetivo"].findData(identificador)
            )
            fila["cantidad"].setText(self._texto_numero(item.cantidad))
        self.boton_guardar.setText("✓  Guardar cambios")
        self._cambiar_tipo()

    def _limpiar_formulario(self):
        self.promocion_editada_id = None
        self.campo_nombre.clear()
        self.combo_tipo.setCurrentIndex(0)
        defectos = {
            "cantidad_lleva": "2",
            "cantidad_paga": "1",
            "porcentaje": "15",
            "porcentaje_maximo": "50",
            "cantidad_minima": "1",
        }
        for clave, (_contenedor, campo) in self.campos_regla.items():
            campo.setText(defectos.get(clave, ""))
        self.check_repetible.setChecked(True)
        self.check_acumulable.setChecked(False)
        self.combo_prioridad.setCurrentIndex(1)
        while len(self.filas_alcance) > self.CANTIDAD_SLOTS_INICIALES:
            self._quitar_fila_alcance(self.filas_alcance[-1])
        for fila in self.filas_alcance:
            fila["alcance"].setCurrentIndex(0)
            self._cargar_objetivos(
                fila["alcance"], fila["objetivo"], conservar=False
            )
            fila["objetivo"].setCurrentIndex(-1)
            fila["objetivo"].lineEdit().clear()
            fila["cantidad"].setText("1")
        self.boton_guardar.setText("✓  Crear promoción")
        self.tabla.clearSelection()
        self._actualizar_botones_tabla()
        self._cambiar_tipo()

    def alternar(self):
        promocion = self._promocion_seleccionada()
        if promocion is None:
            return
        accion = "desactivar" if promocion.activa else "activar"
        respuesta = QMessageBox.question(
            self,
            f"Confirmar {accion}",
            f"¿Querés {accion} la promoción “{promocion.nombre}”?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        try:
            desactivar_promocion(promocion.id, self.usuario.id)
        except ErrorPromocion as error:
            QMessageBox.warning(self, "No se pudo actualizar", str(error))
            return
        self._refrescar_tabla()

    def _ajustar_columnas_tabla(self):
        if not hasattr(self, "tabla"):
            return
        ancho = self.tabla.viewport().width()
        if ancho <= 0:
            return
        proporciones = (0.20, 0.18, 0.34, 0.12, 0.09, 0.07)
        anchos = [int(ancho * p) for p in proporciones]
        anchos[-1] += ancho - sum(anchos)
        for columna, ancho_columna in enumerate(anchos):
            self.tabla.setColumnWidth(columna, ancho_columna)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        QTimer.singleShot(0, self._ajustar_columnas_tabla)