ESTILO_GLOBAL = """
/* ======================== BASE ======================== */
QWidget, QDialog {
    background-color: #f4f6f8;
    color: #172033;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QLabel { background: transparent; color: #172033; }

/* ======================= TÍTULOS ======================= */
QLabel#titulo_nepos {
    color: #101827;
    font-family: "Montserrat", "Segoe UI", sans-serif;
    font-size: 48px;
    font-weight: 900;
    padding: 0;
}
QLabel#titulo_modulo {
    color: #101827;
    font-size: 23px;
    font-weight: 900;
    padding: 4px 0;
}
QLabel#subtitulo {
    color: #64748b;
    font-size: 12px;
}

/* ======================= TARJETAS ======================= */
QFrame#tarjeta, QWidget#tarjeta {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
}

/* ======================== CAMPOS ======================== */
QLineEdit, QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #172033;
    border: 1px solid #aeb8c6;
    border-radius: 7px;
    padding: 8px 10px;
    selection-background-color: #12aa52;
    selection-color: #ffffff;
}
QComboBox::drop-down { width: 28px; border: none; }
QLineEdit:focus, QComboBox:focus, QTextEdit:focus,
QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #12aa52;
}
QLineEdit:disabled, QComboBox:disabled, QTextEdit:disabled,
QDateEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #edf0f3;
    color: #7a8494;
    border-color: #cbd5e1;
}

/* ======================= BOTONES ======================== */
QPushButton {
    background-color: #e2e5e9;
    color: #172033;
    border: 1px solid transparent;
    border-radius: 7px;
    padding: 8px 13px;
    font-weight: 600;
}
QPushButton:hover { background-color: #d3d8de; }
QPushButton:pressed { background-color: #c4cad2; }
QPushButton:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
    border-color: #d4d8de;
}

QPushButton#primario, QPushButton#pestana_activa {
    background-color: #12aa52;
    color: #ffffff;
    border: 1px solid #0e9849;
    font-weight: 800;
}
QPushButton#primario:hover, QPushButton#pestana_activa:hover {
    background-color: #0d9245;
}
QPushButton#primario:pressed, QPushButton#pestana_activa:pressed {
    background-color: #087b3a;
}

QPushButton#peligro {
    background-color: #ffffff;
    color: #b42318;
    border: 1px solid #efb4ae;
    font-weight: 700;
}
QPushButton#peligro:hover { background-color: #fff1f0; }
QPushButton#peligro:pressed { background-color: #fce3e1; }

/* ======================== TABLAS ========================= */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #eef1f4;
    color: #172033;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    gridline-color: #e2e8f0;
    selection-background-color: #d8f5e4;
    selection-color: #172033;
}
QHeaderView::section {
    background-color: #ffffff;
    color: #172033;
    border: none;
    border-bottom: 1px solid #cbd5e1;
    padding: 9px;
    font-weight: 800;
}
QTableCornerButton::section {
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #cbd5e1;
}

/* =================== CHECKBOX Y GRUPOS ================== */
QCheckBox { background: transparent; color: #334155; spacing: 7px; }
QCheckBox:disabled { color: #94a3b8; }
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 10px;
    margin-top: 10px;
    padding-top: 12px;
    font-weight: 800;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
}
QMessageBox { background-color: #f8fafc; }

/* =================== COLORES DE BOTONES ================= */
QPushButton#buscar_ingreso, QPushButton#buscar_ajuste,
QPushButton#buscar_historial, QPushButton#reimprimir_ticket,
QPushButton#agregar_alcance_promocion {
    background-color: #4da8da;
    color: #ffffff;
    border: 1px solid #3189b9;
    border-radius: 8px;
    font-weight: 800;
}
QPushButton#buscar_ingreso:hover, QPushButton#buscar_ajuste:hover,
QPushButton#buscar_historial:hover, QPushButton#reimprimir_ticket:hover,
QPushButton#agregar_alcance_promocion:hover {
    background-color: #3797cc;
}
QPushButton#buscar_ingreso:pressed, QPushButton#buscar_ajuste:pressed,
QPushButton#buscar_historial:pressed, QPushButton#reimprimir_ticket:pressed,
QPushButton#agregar_alcance_promocion:pressed {
    background-color: #287ca9;
}

QPushButton#guardar_ingreso, QPushButton#registrar_ajuste,
QPushButton#guardar_promocion {
    background-color: rgba(18, 170, 82, 205);
    color: #ffffff;
    border: 1px solid rgba(8, 125, 58, 225);
    border-radius: 8px;
    font-weight: 900;
}
QPushButton#guardar_ingreso:hover, QPushButton#registrar_ajuste:hover,
QPushButton#guardar_promocion:hover {
    background-color: rgba(18, 170, 82, 230);
}
QPushButton#guardar_ingreso:pressed, QPushButton#registrar_ajuste:pressed,
QPushButton#guardar_promocion:pressed {
    background-color: rgba(13, 146, 69, 245);
}

QPushButton#borrar_ingreso, QPushButton#anular_venta_historial,
QPushButton#desactivar_promocion {
    background-color: #f08a7c;
    color: #5f2118;
    border: 1px solid #dd7466;
    border-radius: 8px;
    font-weight: 800;
}
QPushButton#borrar_ingreso:hover, QPushButton#anular_venta_historial:hover,
QPushButton#desactivar_promocion:hover { background-color: #e77969; }
QPushButton#borrar_ingreso:pressed, QPushButton#anular_venta_historial:pressed,
QPushButton#desactivar_promocion:pressed { background-color: #d66555; }

QPushButton#nuevo_proveedor, QPushButton#editar_promocion {
    background-color: #887bd4;
    color: #ffffff;
    border: 1px solid #6e61bd;
    border-radius: 8px;
    font-weight: 800;
}
QPushButton#nuevo_proveedor:hover, QPushButton#editar_promocion:hover {
    background-color: #7568c5;
}
QPushButton#nuevo_proveedor:pressed, QPushButton#editar_promocion:pressed {
    background-color: #6255ae;
}

QPushButton#limpiar_historial, QPushButton#nueva_promocion {
    background-color: #dce4ed;
    color: #334155;
    border: 1px solid #c3ceda;
    border-radius: 8px;
    font-weight: 800;
}
QPushButton#limpiar_historial:hover, QPushButton#nueva_promocion:hover {
    background-color: #ccd8e4;
}
QPushButton#limpiar_historial:pressed, QPushButton#nueva_promocion:pressed {
    background-color: #bdcad8;
}

/* ==================== CIERRE DE TURNO ==================== */
QPushButton#cierre_turno {
    background-color: #ef8877;
    color: #5f2118;
    border: 1px solid #df7766;
    border-radius: 22px;
    padding: 0;
    font-weight: 900;
}
QPushButton#cierre_turno:hover { background-color: #e67864; }
QPushButton#cierre_turno:pressed { background-color: #d96755; }
QFrame#separador_cierre { background-color: #873328; border: none; }
QLabel#texto_cierre {
    color: #5f2118;
    font-size: 12px;
    font-weight: 900;
}

/* ================= INGRESO DE MERCADERÍA ================= */
QLabel#producto_encontrado_ingreso {
    background-color: #e5f7ec;
    color: #08783a;
    border: 1px solid #a8dfbd;
    border-radius: 7px;
    padding: 7px 11px;
    font-size: 14px;
    font-weight: 800;
}
QLabel#margen_ingreso {
    background-color: #eefaf3;
    color: #079447;
    border: 1px solid #b6e5c8;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 17px;
    font-weight: 900;
}
QLabel#grupo_ingreso {
    background-color: #f8fafc;
    color: #64748b;
    border: 1px solid #d9e0e8;
    border-radius: 6px;
    padding: 5px 9px;
}
QLabel#resumen_ingreso {
    color: #475569;
    font-weight: 700;
    padding: 0 8px;
}
QPushButton#agregar_ingreso {
    background-color: #25b862;
    color: #ffffff;
    border: 1px solid #15984d;
    border-radius: 8px;
    font-weight: 900;
}
QPushButton#agregar_ingreso:hover { background-color: #19a856; }
QPushButton#agregar_ingreso:pressed { background-color: #108943; }

/* ==================== AJUSTE DE STOCK ==================== */
QLabel#producto_ajuste {
    background-color: #e5f7ec;
    color: #08783a;
    border: 1px solid #a8dfbd;
    border-radius: 7px;
    padding: 7px 12px;
    font-size: 15px;
    font-weight: 900;
}
QLabel#stock_actual_ajuste {
    background-color: #e8f3fb;
    color: #256184;
    border: 1px solid #b5d4e7;
    border-radius: 7px;
    padding: 7px 12px;
    font-weight: 800;
}
QLabel#diferencia_ajuste {
    background-color: #eef2f6;
    color: #64748b;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 7px 12px;
    font-weight: 800;
}
QLabel#estado_busqueda_ajuste {
    background-color: #fff2f1;
    color: #b42318;
    border: 1px solid #efb4ae;
    border-radius: 6px;
    padding: 6px 10px;
    font-weight: 700;
}
QLabel#titulo_historial_ajuste, QLabel#titulo_tabla_historial {
    color: #172033;
    font-size: 14px;
    font-weight: 900;
    padding: 4px 6px;
}

/* ================== HISTORIAL DE VENTAS ================== */
QLabel#titulo_detalle_historial {
    color: #334155;
    font-weight: 800;
    padding: 3px 6px;
}
QPushButton#reimprimir_ticket:disabled {
    background-color: #dbe4ea;
    color: #94a3b8;
    border-color: #cbd5e1;
}
QPushButton#anular_venta_historial:disabled {
    background-color: #f2dddd;
    color: #b98b84;
    border-color: #e3c6c2;
}

/* ====================== PROMOCIONES ====================== */
QLabel#titulo_alcance_promocion, QLabel#titulo_tabla_promociones {
    color: #172033;
    font-size: 14px;
    font-weight: 900;
    padding: 3px 4px;
}
QWidget#contenedor_alcances_promocion,
QWidget#contenedor_acciones_promocion { background: transparent; }
QFrame#tarjeta_alcance_promocion {
    background-color: #f8fafc;
    border: 1px solid #d7dde5;
    border-radius: 8px;
}
QFrame#tarjeta_alcance_promocion:hover {
    background-color: #f2f8f5;
    border-color: #8fd5ad;
}

QPushButton#opcion_promocion {
    background-color: #ffffff;
    color: #475569;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 13px;
    text-align: left;
    font-weight: 700;
}
QPushButton#opcion_promocion:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}
QPushButton#opcion_promocion:checked {
    background-color: #e5f7ec;
    color: #08783a;
    border-color: #55bf7a;
    font-weight: 800;
}
QPushButton#opcion_promocion:checked:hover {
    background-color: #d7f2e1;
    border-color: #3aa561;
}
QLabel#etiqueta_prioridad_promocion {
    color: #475569;
    font-weight: 700;
    padding-left: 6px;
}

QPushButton#quitar_alcance_promocion {
    background-color: #f5d5d1;
    color: #9b3429;
    border: 1px solid #e5aaa3;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 900;
    padding: 0;
}
QPushButton#quitar_alcance_promocion:hover { background-color: #efbcb5; }
QPushButton#quitar_alcance_promocion:pressed { background-color: #e5aaa3; }
QPushButton#activar_promocion {
    background-color: #55bf7a;
    color: #ffffff;
    border: 1px solid #3aa561;
    border-radius: 8px;
    font-weight: 800;
}
QPushButton#activar_promocion:hover { background-color: #42ae68; }
QPushButton#activar_promocion:pressed { background-color: #339957; }
QPushButton#alternar_promocion:disabled,
QPushButton#editar_promocion:disabled {
    background-color: #e5e7eb;
    color: #9ca3af;
    border: 1px solid #d4d8de;
}

/* ================= SCROLL DE PROMOCIONES ================= */
QScrollArea#scroll_principal_promociones {
    background: transparent;
    border: none;
}
QWidget#contenido_promociones { background-color: #f4f6f8; }
QScrollArea#scroll_principal_promociones QScrollBar:vertical {
    background-color: #edf0f3;
    width: 13px;
    margin: 2px;
    border-radius: 6px;
}
QScrollArea#scroll_principal_promociones QScrollBar::handle:vertical {
    background-color: #aeb8c6;
    min-height: 35px;
    border-radius: 6px;
}
QScrollArea#scroll_principal_promociones QScrollBar::handle:vertical:hover {
    background-color: #8f9baa;
}
QScrollArea#scroll_principal_promociones QScrollBar::add-line:vertical,
QScrollArea#scroll_principal_promociones QScrollBar::sub-line:vertical {
    height: 0;
}
"""


def configurar_boton_primario(boton):
    boton.setObjectName("primario")
    return boton


def configurar_boton_peligro(boton):
    boton.setObjectName("peligro")
    return boton