from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import joinedload, selectinload

from database.conexion import nueva_sesion
from database.modelos import (
    DetalleVenta,
    Producto,
    Turno,
    Usuario,
    Venta,
)


def _convertir_fecha(valor, nombre):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(
        f"{nombre} debe tener formato AAAA-MM-DD o DD/MM/AAAA."
    )


def listar_ventas(fecha_desde=None, fecha_hasta=None, turno_id=None, usuario_id=None, limite=200):
    fecha_desde = _convertir_fecha(fecha_desde, "La fecha Desde")
    fecha_hasta = _convertir_fecha(fecha_hasta, "La fecha Hasta")
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ValueError(
            "La fecha Desde no puede ser posterior a la fecha Hasta."
        )

    db = nueva_sesion()
    try:
        query = (
            db.query(Venta)
            .options(
                joinedload(Venta.usuario),
                joinedload(Venta.turno_rel),
                joinedload(Venta.anulada_por),
                joinedload(Venta.items)
                .joinedload(DetalleVenta.producto)
                .joinedload(Producto.categoria_rel),
                selectinload(Venta.promociones_aplicadas),
            )
            .order_by(Venta.fecha.desc())
        )
        if fecha_desde:
            inicio = datetime.combine(fecha_desde, time.min)
            query = query.filter(Venta.fecha >= inicio)
        if fecha_hasta:
            fin_exclusivo = datetime.combine(
                fecha_hasta + timedelta(days=1),
                time.min,
            )
            query = query.filter(Venta.fecha < fin_exclusivo)
        if turno_id:
            query = query.filter(Venta.turno_id == turno_id)
        if usuario_id:
            query = query.filter(Venta.usuario_id == usuario_id)
        return query.limit(limite).all()
    finally:
        db.close()


def listar_cajeros():
    db = nueva_sesion()
    try:
        return db.query(Usuario).order_by(Usuario.nombre).all()
    finally:
        db.close()