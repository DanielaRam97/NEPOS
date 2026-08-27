from sqlalchemy.orm import joinedload
from database.conexion import nueva_sesion
from database.modelos import (
    AjusteStock,
    MovimientoStock,
    Producto,
    Usuario,
)
from utils.validacion import convertir_decimal_finito
from services.auditoria_service import crear_registro_auditoria

class ErrorAjuste(Exception):
    pass


def buscar_producto_por_codigo(codigo):
    db = nueva_sesion()
    try:
        return (
            db.query(Producto)
            .options(joinedload(Producto.categoria_rel))
            .filter(Producto.codigo == codigo)
            .first()
        )
    finally:
        db.close()


def registrar_ajuste(*, codigo_producto, stock_fisico, motivo, usuario_id):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorAjuste("El motivo es obligatorio.")
    try:
        stock_fisico = convertir_decimal_finito(
            stock_fisico,
            nombre="El stock físico",
            minimo=0,
            maximo=100000000,
            decimales=3,
        )
    except ValueError as error:
        raise ErrorAjuste(str(error)) from error

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if (
            not usuario
            or not bool(usuario.activo)
            or usuario.rol not in ("ADMIN", "SUPERVISOR")
        ):
            raise ErrorAjuste(
                "Solamente ADMIN o SUPERVISOR pueden ajustar stock."
            )
        producto = db.query(Producto).filter(Producto.codigo == codigo_producto).first()
        if not producto:
            raise ErrorAjuste(f"No existe el producto con código '{codigo_producto}'.")

        stock_anterior = producto.stock
        diferencia = round(stock_fisico - stock_anterior, 3)
        if diferencia == 0:
            raise ErrorAjuste("El stock físico es igual al actual, no hay nada que ajustar.")

        db.add(
            AjusteStock(
                producto_id=producto.id,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_fisico,
                diferencia=diferencia,
                motivo=motivo,
                usuario_id=usuario_id,
            )
        )
        
        db.add(
            MovimientoStock(
                producto_id=producto.id,
                usuario_id=usuario_id,
                tipo="AJUSTE_STOCK",
                cantidad=diferencia,
                stock_anterior=stock_anterior,
                stock_nuevo=stock_fisico,
                motivo=motivo,
            )
        )
        
        db.add(
            crear_registro_auditoria(
                accion="STOCK_AJUSTADO",
                entidad="PRODUCTO",
                entidad_id=producto.id,
                usuario_id=usuario_id,
                nivel="ADVERTENCIA",
                detalle={
                    "codigo": producto.codigo,
                    "producto": producto.descripcion,
                    "stock_anterior": stock_anterior,
                    "stock_nuevo": stock_fisico,
                    "diferencia": diferencia,
                    "motivo": motivo,
                },
            )
        )
        
        producto.stock = stock_fisico
        db.commit()
        return {"diferencia": diferencia, "stock_anterior": stock_anterior, "stock_nuevo": stock_fisico}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def listar_historial(codigo_producto=None, limite=50):
    db = nueva_sesion()
    try:
        query = (
            db.query(AjusteStock)
            .options(joinedload(AjusteStock.producto), joinedload(AjusteStock.usuario))
            .order_by(AjusteStock.fecha.desc())
        )
        if codigo_producto:
            query = query.join(Producto).filter(Producto.codigo == codigo_producto)
        return query.limit(limite).all()
    finally:
        db.close()
