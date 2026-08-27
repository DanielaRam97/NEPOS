from datetime import datetime
import math

from sqlalchemy.orm import joinedload

from database.conexion import nueva_sesion
from database.modelos import (
    DetalleVenta,
    MovimientoStock,
    Producto,
    Turno,
    Usuario,
    Venta,
    VentaPromocion,
)
from services.auditoria_service import crear_registro_auditoria
from services.configuracion_service import (
    obtener_booleano,
    obtener_decimal,
    redondear_importe,
)
from services.iva_service import tasa_iva_producto
from services.promocion_service import calcular_descuento_promociones

CANTIDAD_MAXIMA = 100
RECARGO_CIGARRILLOS_DEFAULT = 0.15
RECARGO_CREDITO_DEFAULT = 0.15
CATEGORIA_CIGARRILLOS = "CIGARRILLOS"
CUOTAS_VALIDAS = (1, 3, 6, 12)
MEDIOS_INDIVIDUALES = ("EFECTIVO", "QR", "DEBITO", "CREDITO")
FORMAS_PAGO_VALIDAS = MEDIOS_INDIVIDUALES + ("COMBINADO", "AMBOS")
MEDIOS_ELECTRONICOS = {"QR", "DEBITO", "CREDITO"}

# Configuración temporal. También puede administrarse desde configuración de Caja.
PERMITIR_STOCK_NEGATIVO = True

PREFIJO_BALANZA = "20"
LARGO_PLU = 5
LARGO_PESO = 5


class ErrorVenta(Exception):
    pass


def _nombre_categoria(producto):
    if not producto.categoria_rel:
        return ""
    return (producto.categoria_rel.nombre or "").upper()


def buscar_producto(codigo):
    db = nueva_sesion()
    try:
        return (
            db.query(Producto)
            .options(
                joinedload(Producto.categoria_rel),
                joinedload(Producto.proveedor_rel),
            )
            .filter(Producto.codigo == codigo, Producto.activo == 1)
            .first()
        )
    finally:
        db.close()


def buscar_producto_por_plu(plu):
    db = nueva_sesion()
    try:
        return (
            db.query(Producto)
            .options(
                joinedload(Producto.categoria_rel),
                joinedload(Producto.proveedor_rel),
            )
            .filter(Producto.plu == plu, Producto.activo == 1)
            .first()
        )
    finally:
        db.close()


def _digito_verificador_ean13(doce_digitos):
    total = 0
    for indice, caracter in enumerate(doce_digitos):
        peso = 1 if indice % 2 == 0 else 3
        total += int(caracter) * peso
    return (10 - (total % 10)) % 10


def interpretar_codigo_balanza(codigo):
    if (
        len(codigo) != 13
        or not codigo.isdigit()
        or not codigo.startswith(PREFIJO_BALANZA)
    ):
        return None

    doce_digitos = codigo[:12]
    if _digito_verificador_ean13(doce_digitos) != int(codigo[12]):
        return None

    plu = codigo[2 : 2 + LARGO_PLU]
    gramos = int(
        codigo[
            2 + LARGO_PLU : 2 + LARGO_PLU + LARGO_PESO
        ]
    )
    return {"plu": plu, "peso_kg": gramos / 1000}


def generar_codigo_balanza(plu, peso_kg):
    plu = plu.zfill(LARGO_PLU)
    gramos = str(int(round(peso_kg * 1000))).zfill(LARGO_PESO)
    doce_digitos = PREFIJO_BALANZA + plu + gramos
    return doce_digitos + str(_digito_verificador_ean13(doce_digitos))


def validar_cantidad(cantidad, es_pesable=False):
    try:
        cantidad = float(cantidad)
    except (TypeError, ValueError):
        raise ErrorVenta("La cantidad debe ser numérica.")
    if not math.isfinite(cantidad):
        raise ErrorVenta("La cantidad debe ser un número finito.")

    if cantidad <= 0:
        raise ErrorVenta(
            "La cantidad debe ser mayor que cero."
        )

    if cantidad > CANTIDAD_MAXIMA:
        raise ErrorVenta(
            f"La cantidad máxima permitida es {CANTIDAD_MAXIMA}."
        )

    if not es_pesable and not cantidad.is_integer():
        raise ErrorVenta(
            "Los productos por unidad no permiten cantidades decimales."
        )


def calcular_recargo_cigarrillos(
    carrito,
    forma_pago=None,
    cigarrillos_en_efectivo=False,
):
    """Calcula el recargo de los cigarrillos según el pago."""

    if cigarrillos_en_efectivo:
        return 0.0

    if forma_pago == "EFECTIVO":
        return 0.0

    subtotal = sum(
        float(
            item.get(
                "subtotal",
                item.get("total", 0),
            )
        )
        for item in carrito
        if (item.get("categoria") or "").upper()
        == CATEGORIA_CIGARRILLOS
    )

    try:
        tasa = obtener_decimal(
            "RECARGO_CIGARRILLOS"
        )
    except Exception:
        tasa = RECARGO_CIGARRILLOS_DEFAULT

    return round(subtotal * tasa, 2)


def calcular_recargo_credito(subtotal):
    try:
        tasa = obtener_decimal(
            "RECARGO_CREDITO"
        )
    except Exception:
        tasa = RECARGO_CREDITO_DEFAULT

    return round(
        float(subtotal) * tasa,
        2,
    )


def _importe(valor):
    if valor is None:
        return 0.0
    try:
        importe = round(float(valor), 2)
    except (TypeError, ValueError):
        raise ErrorVenta("Los importes de pago deben ser numéricos.")
    if not math.isfinite(importe):
        raise ErrorVenta("Los importes de pago deben ser números finitos.")
    if importe < 0:
        raise ErrorVenta("Los importes de pago no pueden ser negativos.")
    return importe


def _medios_e_importes(
    forma_pago,
    *,
    monto_efectivo,
    monto_qr,
    monto_debito,
    monto_credito,
):
    importes = {
        "EFECTIVO": _importe(monto_efectivo),
        "QR": _importe(monto_qr),
        "DEBITO": _importe(monto_debito),
        "CREDITO": _importe(monto_credito),
    }
    if forma_pago in MEDIOS_INDIVIDUALES:
        return {forma_pago}, importes
    if forma_pago == "AMBOS":
        medios = {
            medio
            for medio in ("EFECTIVO", "QR")
            if importes[medio] > 0
        }
    else:
        medios = {
            medio
            for medio, importe in importes.items()
            if importe > 0
        }
    if len(medios) != 2:
        raise ErrorVenta(
            "El pago combinado debe usar exactamente dos medios distintos."
        )
    return medios, importes


def registrar_venta(
    usuario_id,
    turno_id,
    forma_pago,
    items,
    monto_efectivo=None,
    monto_qr=None,
    monto_debito=None,
    monto_credito=None,
    cigarrillos_en_efectivo=False,
    cuotas=None,
    monto_recibido=None,
):
    if not items:
        raise ErrorVenta("La venta no tiene productos.")
    if forma_pago not in FORMAS_PAGO_VALIDAS:
        raise ErrorVenta("Forma de pago inválida.")

    medios, importes = _medios_e_importes(
        forma_pago,
        monto_efectivo=monto_efectivo,
        monto_qr=monto_qr,
        monto_debito=monto_debito,
        monto_credito=monto_credito,
    )
    if "CREDITO" in medios and cuotas not in CUOTAS_VALIDAS:
        raise ErrorVenta(
            f"Cuotas inválidas. Debe ser una de: {CUOTAS_VALIDAS}."
        )

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ErrorVenta("La sesión del operador no está activa.")
        if usuario.rol not in ("CAJERO", "SUPERVISOR", "ADMIN"):
            raise ErrorVenta(
                "El operador no tiene permiso para registrar ventas."
            )

        turno = db.get(Turno, turno_id)
        if not turno or turno.estado != "ABIERTO":
            raise ErrorVenta(
                "El turno ya no está abierto. Volvé a iniciar sesión."
            )
        if turno.usuario_id != usuario_id:
            raise ErrorVenta(
                "El turno abierto no pertenece al operador actual."
            )

        permitir_stock_negativo = obtener_booleano(
            "PERMITIR_STOCK_NEGATIVO", db
        )
        tasa_cigarrillos = obtener_decimal(
            "RECARGO_CIGARRILLOS", db
        )
        tasa_credito = obtener_decimal("RECARGO_CREDITO", db)

        detalles = []
        subtotal_general = 0.0
        subtotal_cigarrillos = 0.0

        for item in items:
            producto = (
                db.query(Producto)
                .options(joinedload(Producto.categoria_rel))
                .filter(Producto.codigo == item["codigo"])
                .with_for_update()
                .first()
            )
            if not producto or not producto.activo:
                raise ErrorVenta(
                    f"Producto {item['codigo']} no encontrado."
                )

            cantidad = float(item["cantidad"])
            validar_cantidad(
                cantidad,
                es_pesable=bool(producto.pesable),
            )
            pendiente = bool(
                getattr(producto, "pendiente_revision", False)
            )
            if (
                not permitir_stock_negativo
                and not pendiente
                and float(producto.stock or 0) < cantidad
            ):
                raise ErrorVenta(
                    f"Stock insuficiente de {producto.descripcion}."
                )

            subtotal = redondear_importe(
                float(producto.precio or 0) * cantidad,
                db,
            )
            subtotal_general += subtotal
            if _nombre_categoria(producto) == CATEGORIA_CIGARRILLOS:
                subtotal_cigarrillos += subtotal

            detalles.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "precio_unitario": float(producto.precio or 0),
                    "costo_unitario": float(producto.costo or 0),
                    "subtotal": subtotal,
                    "iva_tasa": tasa_iva_producto(producto),
                }
            )
        descuento_promociones, aplicaciones_promo = (
            calcular_descuento_promociones(items, db=db)
        )
        subtotal_general = redondear_importe(subtotal_general, db)
        descuento_promociones = redondear_importe(
            descuento_promociones,
            db,
        )
        subtotal_con_descuento = redondear_importe(
            subtotal_general - descuento_promociones,
            db,
        )
        subtotal_cigarrillos = redondear_importe(
            subtotal_cigarrillos, db
        )
        recargo_cigarrillos = 0.0
        if (
            medios & MEDIOS_ELECTRONICOS
            and not cigarrillos_en_efectivo
        ):
            recargo_cigarrillos = redondear_importe(
                subtotal_cigarrillos * tasa_cigarrillos,
                db,
            )
        recargo_credito = 0.0
        if "CREDITO" in medios:
            recargo_credito = redondear_importe(
                subtotal_con_descuento * tasa_credito,
                db,
            )
        recargo = redondear_importe(
            recargo_cigarrillos + recargo_credito,
            db,
        )
        total = redondear_importe(
            subtotal_con_descuento + recargo,
            db,
        )

        if forma_pago in MEDIOS_INDIVIDUALES:
            importes = {medio: 0.0 for medio in MEDIOS_INDIVIDUALES}
            importes[forma_pago] = total
        else:
            suma = redondear_importe(sum(importes.values()), db)
            if suma != total:
                raise ErrorVenta(
                    "La suma de los medios debe coincidir con el total "
                    f"de la venta (${total:.2f})."
                )

        if cigarrillos_en_efectivo:
            if importes["EFECTIVO"] < subtotal_cigarrillos:
                raise ErrorVenta(
                    "El efectivo debe cubrir el subtotal de cigarrillos "
                    f"(${subtotal_cigarrillos:.2f})."
                )

        vuelto = 0.0
        efectivo_aplicado = importes["EFECTIVO"]
        if efectivo_aplicado > 0:
            recibido = (
                efectivo_aplicado
                if monto_recibido is None
                else _importe(monto_recibido)
            )
            if recibido < efectivo_aplicado:
                raise ErrorVenta(
                    "El efectivo recibido debe cubrir "
                    f"${efectivo_aplicado:.2f}."
                )
            vuelto = redondear_importe(
                recibido - efectivo_aplicado,
                db,
            )
            monto_recibido = recibido
        else:
            monto_recibido = None

        venta = Venta(
            usuario_id=usuario_id,
            turno_id=turno_id,
            forma_pago=forma_pago,
            subtotal=subtotal_general,
            recargo=recargo,
            descuento_promociones=descuento_promociones,
            total=total,
            efectivo=importes["EFECTIVO"],
            qr=importes["QR"],
            debito=importes["DEBITO"],
            credito=importes["CREDITO"],
            cuotas=cuotas if "CREDITO" in medios else None,
            monto_recibido=monto_recibido,
            vuelto=vuelto,
        )
        db.add(venta)
        db.flush()
        venta.numero = venta.id

        for aplicacion in aplicaciones_promo:
            db.add(
                VentaPromocion(
                    venta_id=venta.id,
                    promocion_id=aplicacion["promocion_id"],
                    nombre=aplicacion["promocion"],
                    tipo=aplicacion["tipo"],
                    veces=aplicacion["veces"],
                    ahorro=aplicacion["ahorro"],
                )
            )

        stocks_negativos = []
        for detalle in detalles:
            producto = detalle["producto"]
            db.add(
                DetalleVenta(
                    venta_id=venta.id,
                    producto_id=producto.id,
                    cantidad=detalle["cantidad"],
                    precio_unitario=detalle["precio_unitario"],
                    costo_unitario=detalle["costo_unitario"],
                    subtotal=detalle["subtotal"],
                    iva_tasa=detalle["iva_tasa"],
                )
            )
            stock_anterior = float(producto.stock or 0)
            stock_nuevo = stock_anterior - detalle["cantidad"]
            producto.stock = stock_nuevo
            if stock_nuevo < 0:
                stocks_negativos.append(
                    {
                        "producto_id": producto.id,
                        "codigo": producto.codigo,
                        "stock_anterior": stock_anterior,
                        "stock_nuevo": stock_nuevo,
                    }
                )
            db.add(
                MovimientoStock(
                    producto_id=producto.id,
                    usuario_id=usuario_id,
                    venta_id=venta.id,
                    tipo="VENTA",
                    cantidad=-detalle["cantidad"],
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_nuevo,
                    motivo=f"Venta N° {venta.numero}",
                )
            )

        db.add(
            crear_registro_auditoria(
                usuario_id=usuario_id,
                turno_id=turno_id,
                venta_id=venta.id,
                accion="VENTA_CONFIRMADA",
                entidad="VENTA",
                entidad_id=venta.id,
                nivel="INFO",
                detalle={
                    "numero": venta.numero,
                    "forma_pago": forma_pago,
                    "medios": sorted(medios),
                    "total": total,
                    "items": len(detalles),
                    "vuelto": vuelto,
                    "descuento_promociones": descuento_promociones,
                    "promociones": aplicaciones_promo,
                },
            )
        )
        if stocks_negativos:
            db.add(
                crear_registro_auditoria(
                    usuario_id=usuario_id,
                    turno_id=turno_id,
                    venta_id=venta.id,
                    accion="STOCK_NEGATIVO_EN_VENTA",
                    entidad="VENTA",
                    entidad_id=venta.id,
                    nivel="ADVERTENCIA",
                    detalle={"productos": stocks_negativos},
                )
            )
        db.commit()
        return {
            "numero": venta.numero,
            "total": total,
            "recargo": recargo,
            "descuento_promociones": descuento_promociones,
            "aplicaciones_promociones": aplicaciones_promo,
            "efectivo": importes["EFECTIVO"],
            "qr": importes["QR"],
            "debito": importes["DEBITO"],
            "credito": importes["CREDITO"],
            "monto_recibido": monto_recibido,
            "vuelto": vuelto,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def anular_venta(venta_id, motivo, usuario_id):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorVenta("El motivo de la anulación es obligatorio.")

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ErrorVenta("La sesión del operador no está activa.")
        if usuario.rol not in ("SUPERVISOR", "ADMIN"):
            raise ErrorVenta(
                "Solo SUPERVISOR o ADMIN pueden anular ventas."
            )

        venta = (
            db.query(Venta)
            .options(joinedload(Venta.items))
            .filter(Venta.id == venta_id)
            .with_for_update()
            .first()
        )
        if not venta:
            raise ErrorVenta("Venta no encontrada.")
        if venta.anulada:
            raise ErrorVenta("Esta venta ya estaba anulada.")

        for item in venta.items:
            producto = (
                db.query(Producto)
                .filter(Producto.id == item.producto_id)
                .with_for_update()
                .first()
            )
            if not producto:
                continue
            stock_anterior = float(producto.stock or 0)
            stock_nuevo = stock_anterior + float(item.cantidad)
            producto.stock = stock_nuevo
            db.add(
                MovimientoStock(
                    producto_id=producto.id,
                    usuario_id=usuario_id,
                    venta_id=venta.id,
                    tipo="ANULACION_VENTA",
                    cantidad=float(item.cantidad),
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_nuevo,
                    motivo=(
                        f"Anulación venta N° {venta.numero}: {motivo}"
                    ),
                )
            )

        venta.anulada = True
        venta.motivo_anulacion = motivo
        venta.anulada_por_id = usuario_id
        venta.fecha_anulacion = datetime.now()
        db.add(
            crear_registro_auditoria(
                usuario_id=usuario_id,
                turno_id=venta.turno_id,
                venta_id=venta.id,
                accion="VENTA_ANULADA",
                entidad="VENTA",
                entidad_id=venta.id,
                detalle={
                    "numero": venta.numero,
                    "motivo": motivo,
                },
                nivel="CRITICO",
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
