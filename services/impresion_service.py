from datetime import datetime
from textwrap import wrap
from services.configuracion_service import (
    obtener_configuracion_comercio,
    obtener_valor,
)


ANCHO_TICKET = 32
CORTE_AUTOMATICO = False

ESC = b"\x1b"
GS = b"\x1d"
INICIALIZAR = ESC + b"@"
ALINEAR_IZQUIERDA = ESC + b"a\x00"
ALINEAR_CENTRO = ESC + b"a\x01"
NEGRITA_SI = ESC + b"E\x01"
NEGRITA_NO = ESC + b"E\x00"
TAMANO_NORMAL = GS + b"!\x00"
TAMANO_DOBLE = GS + b"!\x11"
CORTAR_PAPEL = GS + b"V\x00"


class ErrorImpresion(Exception):
    pass


def _texto(valor):
    return str(valor).encode("cp858", errors="replace")


def _moneda(valor):
    numero = float(valor or 0)
    texto = f"{numero:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${texto}"


def _cantidad(valor):
    numero = float(valor or 0)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def _izquierda_derecha(izquierda, derecha):
    izquierda = str(izquierda)
    derecha = str(derecha)
    disponible = ANCHO_TICKET - len(derecha) - 1
    izquierda = izquierda[:max(disponible, 0)]
    espacios = max(ANCHO_TICKET - len(izquierda) - len(derecha), 1)
    return izquierda + (" " * espacios) + derecha


def _lineas_producto(item):
    descripcion = str(item.get("descripcion") or "Producto").strip()
    cantidad = _cantidad(item.get("cantidad"))
    precio = _moneda(item.get("precio"))
    total = _moneda(item.get("total", item.get("subtotal", 0)))

    lineas = wrap(descripcion, width=ANCHO_TICKET) or [descripcion]
    detalle = f"{cantidad} x {precio}"
    lineas.append(_izquierda_derecha(detalle, total))
    return lineas


def construir_ticket(resultado, carrito, usuario, turno, pago, fecha=None, reimpresion=False, anulada=False,):
    subtotal = round(
        sum(float(item.get("total", item.get("subtotal", 0))) for item in carrito),
        2,
    )
    descuento = float(resultado.get("descuento_promociones", 0) or 0)
    recargo = float(resultado.get("recargo", 0) or 0)
    total = float(resultado.get("total", 0) or 0)
    promociones = resultado.get("aplicaciones_promociones") or []

    ahora = fecha or datetime.now()
    try:
        comercio = obtener_configuracion_comercio()
    except Exception:
        comercio = {
            "nombre": "NEPOS",
            "direccion": "",
            "telefono": "",
            "cuit": "",
        }
    separador = "-" * ANCHO_TICKET
    nombre_ticket = "\n".join(
        wrap(comercio.get("nombre") or "NEPOS", width=16)[:2]
    )
    direccion_ticket = "\n".join(
        wrap(comercio.get("direccion") or "", width=ANCHO_TICKET)[:2]
    )
    partes = [
        INICIALIZAR,
        ALINEAR_CENTRO,
        NEGRITA_SI,
        TAMANO_DOBLE,
        _texto(f"{nombre_ticket}\n"),
        TAMANO_NORMAL,
        _texto(
            (direccion_ticket + "\n")
            if direccion_ticket
            else ""
        ),
        _texto(
            (f"Tel: {comercio['telefono']}\n")
            if comercio.get("telefono")
            else ""
        ),
        _texto(
            (f"CUIT: {comercio['cuit']}\n")
            if comercio.get("cuit")
            else ""
        ),
        _texto("COMPROBANTE DE VENTA\n"),
        _texto(
            "*** REIMPRESION ***\n"
            if reimpresion
            else ""
        ),
        _texto(
            "*** VENTA ANULADA ***\n"
            if anulada
            else ""
        ),
        NEGRITA_NO,
        _texto(separador + "\n"),
        ALINEAR_IZQUIERDA,
        _texto(f"Venta Nro: {resultado.get('numero', '-')}\n"),
        _texto(f"Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}\n"),
        _texto(f"Cajero: {getattr(usuario, 'nombre', '-')}\n"),
        _texto(f"Turno: {getattr(turno, 'turno', '-')}\n"),
        _texto(separador + "\n"),
    ]

    for item in carrito:
        for linea in _lineas_producto(item):
            partes.append(_texto(linea + "\n"))

    partes.extend(
        [
            _texto(separador + "\n"),
            _texto(_izquierda_derecha("Subtotal", _moneda(subtotal)) + "\n"),
        ]
    )

    if descuento > 0:
        partes.append(
            _texto(_izquierda_derecha("Promociones", "-" + _moneda(descuento)) + "\n")
        )
        for aplicacion in promociones:
            nombre = aplicacion.get("promocion", "Promoción")
            veces = int(aplicacion.get("veces", 1) or 1)
            sufijo = f" x{veces}" if veces > 1 else ""
            for linea in wrap(f"  {nombre}{sufijo}", width=ANCHO_TICKET):
                partes.append(_texto(linea + "\n"))

    if recargo > 0:
        partes.append(
            _texto(_izquierda_derecha("Recargos", _moneda(recargo)) + "\n")
        )

    partes.extend(
        [
            NEGRITA_SI,
            _texto(_izquierda_derecha("TOTAL", _moneda(total)) + "\n"),
            NEGRITA_NO,
            _texto(separador + "\n"),
            _texto("MEDIOS DE PAGO\n"),
        ]
    )

    medios = (
        ("Efectivo", resultado.get("efectivo")),
        ("QR / Transferencia", resultado.get("qr")),
        ("Débito", resultado.get("debito")),
        ("Crédito", resultado.get("credito")),
    )
    for nombre, importe in medios:
        if float(importe or 0) > 0:
            partes.append(
                _texto(_izquierda_derecha(nombre, _moneda(importe)) + "\n")
            )

    cuotas = pago.get("cuotas")
    if cuotas:
        partes.append(_texto(f"Cuotas: {cuotas}\n"))
    recibido = resultado.get("monto_recibido")
    if recibido is not None:
        partes.append(
            _texto(_izquierda_derecha("Recibido", _moneda(recibido)) + "\n")
        )
    vuelto = float(resultado.get("vuelto", 0) or 0)
    if vuelto > 0:
        partes.append(
            _texto(_izquierda_derecha("Vuelto", _moneda(vuelto)) + "\n")
        )

    partes.extend(
        [
            _texto(separador + "\n"),
            ALINEAR_CENTRO,
            NEGRITA_SI,
            _texto("GRACIAS POR SU COMPRA\n"),
            NEGRITA_NO,
            _texto("Comprobante no fiscal\n"),
            _texto("\n\n\n\n"),
        ]
    )
    if CORTE_AUTOMATICO:
        partes.append(CORTAR_PAPEL)
    return b"".join(partes)


def listar_impresoras():
    try:
        import win32print
    except ImportError as error:
        raise ErrorImpresion(
            "Falta pywin32. Ejecutá: python -m pip install pywin32"
        ) from error
    try:
        impresoras = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )
    except Exception as error:
        codigo = getattr(error, "winerror", None)
        if codigo is None and getattr(error, "args", None):
            codigo = error.args[0]

        # 1722: RPC no disponible. 1060/1062: servicio de impresión ausente
        # o detenido. La impresora es opcional, por lo que estas condiciones
        # deben comportarse igual que una PC sin impresoras instaladas.
        if codigo in (1060, 1062, 1722):
            return []

        raise ErrorImpresion(
            f"Windows no permitió consultar las impresoras: {error}"
        ) from error

    return sorted(
        {impresora[2] for impresora in impresoras},
        key=str.casefold,
    )


def imprimir_datos(datos, nombre_impresora=None):
    try:
        import win32print
    except ImportError as error:
        raise ErrorImpresion(
            "Falta pywin32. Ejecutá: python -m pip install pywin32"
        ) from error

    nombre_impresora = (
        nombre_impresora
        or obtener_valor("NOMBRE_IMPRESORA")
        or ""
    ).strip()
    if not nombre_impresora:
        raise ErrorImpresion(
            "No hay una impresora configurada. Seleccionala en Configuración."
        )
    disponibles = listar_impresoras()
    if nombre_impresora not in disponibles:
        raise ErrorImpresion(
            f"No se encontró la impresora '{nombre_impresora}'."
        )

    manejador = None
    documento_iniciado = False
    pagina_iniciada = False
    try:
        manejador = win32print.OpenPrinter(nombre_impresora)
        trabajo = win32print.StartDocPrinter(
            manejador,
            1,
            ("Ticket de venta NEPOS", None, "RAW"),
        )
        documento_iniciado = True
        win32print.StartPagePrinter(manejador)
        pagina_iniciada = True
        win32print.WritePrinter(manejador, datos)
        return trabajo
    except Exception as error:
        raise ErrorImpresion(str(error)) from error
    finally:
        if manejador is not None:
            if pagina_iniciada:
                win32print.EndPagePrinter(manejador)
            if documento_iniciado:
                win32print.EndDocPrinter(manejador)
            win32print.ClosePrinter(manejador)


def imprimir_prueba(nombre_impresora=None, comercio=None):
    comercio = comercio or obtener_configuracion_comercio()
    nombre = (comercio.get("nombre") or "NEPOS").strip()
    direccion = (comercio.get("direccion") or "").strip()
    telefono = (comercio.get("telefono") or "").strip()
    cuit = (comercio.get("cuit") or "").strip()
    encabezado = [
        INICIALIZAR,
        ALINEAR_CENTRO,
        NEGRITA_SI,
        _texto("\n".join(wrap(nombre, width=ANCHO_TICKET)) + "\n"),
        NEGRITA_NO,
    ]
    if direccion:
        encabezado.append(
            _texto("\n".join(wrap(direccion, width=ANCHO_TICKET)) + "\n")
        )
    if telefono:
        encabezado.append(_texto(f"Tel: {telefono}\n"))
    if cuit:
        encabezado.append(_texto(f"CUIT: {cuit}\n"))

    datos = b"".join(
        encabezado
        + [
            _texto("PRUEBA DE IMPRESION\n"),
            _texto(datetime.now().strftime("%d/%m/%Y %H:%M\n")),
            _texto("-" * ANCHO_TICKET + "\n"),
            _texto("Impresora configurada correctamente\n\n\n"),
        ]
    )
    return imprimir_datos(datos, nombre_impresora)


def imprimir_ticket_venta(resultado, carrito, usuario, turno, pago):
    datos = construir_ticket(resultado, carrito, usuario, turno, pago)
    return imprimir_datos(datos)

def imprimir_ticket_historico(venta):
    carrito = []

    for detalle in venta.items:
        descripcion = (
            detalle.producto.descripcion
            if detalle.producto
            else "(producto eliminado)"
        )

        carrito.append(
            {
                "descripcion": descripcion,
                "cantidad": float(detalle.cantidad or 0),
                "precio": float(
                    detalle.precio_unitario or 0
                ),
                "subtotal": float(detalle.subtotal or 0),
                "total": float(detalle.subtotal or 0),
            }
        )

    resultado = {
        "numero": venta.numero or venta.id,
        "descuento_promociones": float(
            getattr(
                venta,
                "descuento_promociones",
                0,
            )
            or 0
        ),
        "aplicaciones_promociones": [],
        "recargo": float(venta.recargo or 0),
        "total": float(venta.total or 0),
        "efectivo": float(venta.efectivo or 0),
        "qr": float(venta.qr or 0),
        "debito": float(venta.debito or 0),
        "credito": float(venta.credito or 0),
        "monto_recibido": getattr(
            venta,
            "monto_recibido",
            None,
        ),
        "vuelto": float(
            getattr(venta, "vuelto", 0) or 0
        ),
    }

    pago = {
        "cuotas": getattr(venta, "cuotas", None),
    }

    datos = construir_ticket(
        resultado=resultado,
        carrito=carrito,
        usuario=venta.usuario,
        turno=venta.turno_rel,
        pago=pago,
        fecha=venta.fecha,
        reimpresion=True,
        anulada=bool(venta.anulada),
    )

    return imprimir_datos(datos)