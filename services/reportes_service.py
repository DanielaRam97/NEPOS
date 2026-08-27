from sqlalchemy import func
from database.conexion import nueva_sesion
from database.modelos import Venta, DetalleVenta, Producto


def resumen_periodo(fecha_desde=None, fecha_hasta=None):
    db = nueva_sesion()
    try:
        query = db.query(Venta).filter(Venta.anulada == False)
        if fecha_desde:
            query = query.filter(Venta.fecha >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(Venta.fecha <= f"{fecha_hasta} 23:59:59")
        ventas = query.all()

        venta_bruta = sum(v.total for v in ventas)
        ganancia = 0.0
        unidades = 0.0

        for venta in ventas:
            for item in venta.items:
                producto = db.query(Producto).get(item.producto_id)
                costo_unitario = producto.costo if producto else 0
                ganancia += item.subtotal - (costo_unitario * item.cantidad)
                unidades += item.cantidad

        return {
            "venta_bruta": round(venta_bruta, 2),
            "transacciones": len(ventas),
            "unidades": round(unidades, 2),
            "ticket_promedio": round(
                venta_bruta / len(ventas),
                2,
            ) if ventas else 0.0,
            "ganancia_estimada": round(ganancia, 2),
        }
    finally:
        db.close()


def ranking_productos(fecha_desde=None, fecha_hasta=None, limite=8):
    db = nueva_sesion()
    try:
        query = (
            db.query(
                Producto.descripcion,
                func.sum(DetalleVenta.cantidad),
                func.sum(DetalleVenta.subtotal),
            )
            .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
            .join(Venta, Venta.id == DetalleVenta.venta_id)
            .filter(Venta.anulada == False)
        )
        
        if fecha_desde:
            query = query.filter(Venta.fecha >= f"{fecha_desde} 00:00:00")
        if fecha_hasta:
            query = query.filter(Venta.fecha <= f"{fecha_hasta} 23:59:59")

        resultados = (
            query.group_by(Producto.id, Producto.descripcion)
            .order_by(func.sum(DetalleVenta.subtotal).desc())
            .limit(limite)
            .all()
        )
        return [
            {"descripcion": descripcion, "unidades": float(unidades), "total": float(total)}
            for descripcion, unidades, total in resultados
        ]
    finally:
        db.close()


def productos_stock_critico(umbral=5):
    db = nueva_sesion()
    try:
        return (
            db.query(Producto)
            .filter(Producto.activo == 1, Producto.stock <= umbral)
            .order_by(Producto.stock)
            .all()
        )
    finally:
        db.close()