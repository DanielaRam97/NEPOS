from datetime import datetime
from database.conexion import nueva_sesion
from database.modelos import DetalleVenta, Producto, Turno, Usuario, Venta
from services.auditoria_service import crear_registro_auditoria
from services.iva_service import separar_iva_incluido, tasa_iva_producto
from utils.validacion import convertir_decimal_finito
from sqlalchemy import func
from sqlalchemy.orm import joinedload


class ErrorCierre(Exception):
    pass


def calcular_resumen(turno_id):
    db = nueva_sesion()
    try:
        turno = db.query(Turno).get(turno_id)
        if not turno:
            raise ErrorCierre("Turno no encontrado.")

        ventas = (
            db.query(Venta)
            .options(
                joinedload(Venta.items)
                .joinedload(DetalleVenta.producto)
                .joinedload(Producto.categoria_rel)
            )
            .filter(
                Venta.turno_id == turno_id,
                Venta.anulada.is_(False),
            )
            .all()
        )

        unidades = 0.0
        pesables = 0.0
        iva_10_5 = 0.0
        iva_21 = 0.0
        neto_10_5 = 0.0
        neto_21 = 0.0

        for venta in ventas:
            subtotales_por_tasa = {10.5: 0.0, 21.0: 0.0}
            for item in venta.items:
                producto = item.producto
                if producto and producto.pesable:
                    pesables += float(item.cantidad or 0)
                else:
                    unidades += float(item.cantidad or 0)

                tasa_guardada = getattr(item, "iva_tasa", None)
                tasa = (
                    float(tasa_guardada)
                    if tasa_guardada is not None
                    else tasa_iva_producto(producto)
                )
                tasa = 10.5 if abs(tasa - 10.5) < 0.01 else 21.0
                subtotales_por_tasa[tasa] += float(item.subtotal or 0)

            subtotal_items = sum(subtotales_por_tasa.values())
            total_fiscal = float(venta.total or 0)
            if subtotal_items > 0:
                for tasa, subtotal_tasa in subtotales_por_tasa.items():
                    total_tasa = total_fiscal * subtotal_tasa / subtotal_items
                    neto, impuesto = separar_iva_incluido(total_tasa, tasa)
                    if tasa == 10.5:
                        neto_10_5 += neto
                        iva_10_5 += impuesto
                    else:
                        neto_21 += neto
                        iva_21 += impuesto

        if turno.estado == "CERRADO":
            if turno.iva_10_5 is not None:
                iva_10_5 = float(turno.iva_10_5)
            if turno.iva_21 is not None:
                iva_21 = float(turno.iva_21)

        efectivo = sum(float(v.efectivo or 0) for v in ventas)
        fondo_inicial = float(turno.fondo_inicial or 0)
        esperado = round(fondo_inicial + efectivo, 2)
        declarado = (
            float(turno.efectivo_declarado)
            if turno.efectivo_declarado is not None
            else None
        )
        diferencia = (
            float(turno.diferencia_caja)
            if turno.diferencia_caja is not None
            else None
        )

        return {
            "turno": turno.turno,
            "cajero": turno.usuario.nombre,
            "fondo_inicial": fondo_inicial,
            "transacciones": len(ventas),
            "unidades": round(unidades, 2),
            "pesables": round(pesables, 2),
            "venta_bruta": round(sum(float(v.total or 0) for v in ventas), 2),
            "recargos": round(sum(float(v.recargo or 0) for v in ventas), 2),
            "iva_10_5": round(iva_10_5, 2),
            "iva_21": round(iva_21, 2),
            "neto_10_5": round(neto_10_5, 2),
            "neto_21": round(neto_21, 2),
            "efectivo": round(efectivo, 2),
            "qr": round(sum(float(v.qr or 0) for v in ventas), 2),
            "debito": round(sum(float(v.debito or 0) for v in ventas), 2),
            "credito": round(sum(float(v.credito or 0) for v in ventas), 2),
            "efectivo_esperado_en_caja": esperado,
            "efectivo_declarado": declarado,
            "diferencia_caja": diferencia,
            "observacion_cierre": turno.observacion_cierre or "",
        }
    finally:
        db.close()


def cerrar_turno(
    turno_id,
    usuario_id,
    *,
    efectivo_declarado,
    observacion_cierre="",
):
    try:
        efectivo_declarado = convertir_decimal_finito(
            efectivo_declarado,
            nombre="El efectivo contado",
            minimo=0,
            maximo=100000000,
            interpretar_punto_miles=True,
        )
    except ValueError as error:
        raise ErrorCierre(str(error)) from error
    observacion_cierre = " ".join(
        (observacion_cierre or "").strip().split()
    )
    if len(observacion_cierre) > 250:
        raise ErrorCierre("La observación no puede superar 250 caracteres.")

    db = nueva_sesion()
    try:
        turno = (
            db.query(Turno)
            .filter(Turno.id == turno_id)
            .with_for_update()
            .first()
        )
        if not turno:
            raise ErrorCierre("Turno no encontrado.")
        if turno.estado == "CERRADO":
            raise ErrorCierre("El turno ya estaba cerrado.")
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not bool(usuario.activo):
            raise ErrorCierre("El usuario no está habilitado.")
        if turno.usuario_id != usuario.id:
            raise ErrorCierre(
                "El turno solamente puede cerrarlo el operador que lo abrió."
            )

        efectivo_ventas = float(
            db.query(func.coalesce(func.sum(Venta.efectivo), 0))
            .filter(
                Venta.turno_id == turno.id,
                Venta.anulada.is_(False),
            )
            .scalar()
            or 0
        )
        esperado = round(float(turno.fondo_inicial or 0) + efectivo_ventas, 2)
        diferencia = round(efectivo_declarado - esperado, 2)
        if abs(diferencia) >= 0.01 and not observacion_cierre:
            raise ErrorCierre(
                "Ingresá una observación para justificar el sobrante o faltante."
            )

        resumen_fiscal = calcular_resumen(turno.id)
        turno.iva_10_5 = resumen_fiscal["iva_10_5"]
        turno.iva_21 = resumen_fiscal["iva_21"]
        turno.estado = "CERRADO"
        turno.fecha_cierre = datetime.now()
        turno.efectivo_declarado = efectivo_declarado
        turno.diferencia_caja = diferencia
        turno.observacion_cierre = observacion_cierre or None
        turno.cerrado_por_id = usuario.id
        db.add(
            crear_registro_auditoria(
                accion="TURNO_CERRADO",
                entidad="TURNO",
                entidad_id=turno.id,
                usuario_id=usuario.id,
                turno_id=turno.id,
                nivel="ADVERTENCIA" if abs(diferencia) >= 0.01 else "INFO",
                detalle={
                    "turno": turno.turno,
                    "efectivo_esperado": esperado,
                    "efectivo_declarado": efectivo_declarado,
                    "diferencia": diferencia,
                    "observacion": observacion_cierre,
                    "iva_10_5": turno.iva_10_5,
                    "iva_21": turno.iva_21,
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def listar_turnos_cerrados(fecha_desde=None, fecha_hasta=None):
    db = nueva_sesion()
    try:
        query = (
            db.query(Turno)
            .options(joinedload(Turno.usuario))
            .filter(Turno.estado == "CERRADO")
            .order_by(Turno.fecha_cierre.desc())
        )
        if fecha_desde:
            query = query.filter(Turno.fecha_cierre >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(Turno.fecha_cierre <= f"{fecha_hasta} 23:59:59")
        return query.all()
    finally:
        db.close()
def registrar_correccion_cierre(turno_id, usuario_id, descripcion):
    descripcion = " ".join((descripcion or "").strip().split())

    if not descripcion:
        raise ErrorCierre("La descripción de la corrección es obligatoria.")
    if len(descripcion) > 500:
        raise ErrorCierre(
            "La descripción no puede superar los 500 caracteres."
        )

    db = nueva_sesion()
    try:
        turno = db.get(Turno, turno_id)
        if not turno:
            raise ErrorCierre("Turno no encontrado.")
        if turno.estado != "CERRADO":
            raise ErrorCierre(
                "Solo se pueden registrar correcciones en turnos cerrados."
            )

        usuario = db.get(Usuario, usuario_id)
        if not usuario or not bool(usuario.activo):
            raise ErrorCierre("El usuario no está habilitado.")
        if usuario.rol != "ADMIN":
            raise ErrorCierre(
                "Solo ADMIN puede registrar correcciones de cierre."
            )

        db.add(
            crear_registro_auditoria(
                accion="CORRECCION_CIERRE",
                entidad="TURNO",
                entidad_id=turno.id,
                turno_id=turno.id,
                usuario_id=usuario.id,
                nivel="ADVERTENCIA",
                detalle={
                    "turno": turno.turno,
                    "descripcion": descripcion,
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()