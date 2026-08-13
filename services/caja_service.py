from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.conexion import nueva_sesion
from database.modelos import Categoria, Producto, Turno, Usuario
from services.auditoria_service import registrar_auditoria


ROLES_CAJA = ("CAJERO", "SUPERVISOR", "ADMIN")


class ErrorCaja(Exception):
    pass


def validar_contexto_caja(usuario_id, turno_id):
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ErrorCaja("La sesión del operador no está activa.")
        if usuario.rol not in ROLES_CAJA:
            raise ErrorCaja("El operador no tiene permiso para usar la caja.")
        turno = db.get(Turno, turno_id)
        if not turno or turno.estado != "ABIERTO":
            raise ErrorCaja("El turno no está abierto.")
        if turno.usuario_id != usuario.id:
            raise ErrorCaja("El turno abierto no pertenece al operador actual.")
        return True
    finally:
        db.close()


def listar_categorias_caja():
    db = nueva_sesion()
    try:
        return db.query(Categoria).order_by(Categoria.nombre).all()
    finally:
        db.close()


def buscar_productos_caja(texto="", categoria_id=None, limite=200):
    db = nueva_sesion()
    try:
        consulta = (
            db.query(Producto)
            .options(joinedload(Producto.categoria_rel), joinedload(Producto.proveedor_rel))
            .filter(Producto.activo == 1)
        )
        texto = (texto or "").strip()
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.filter(or_(
                Producto.codigo.ilike(patron),
                Producto.plu.ilike(patron),
                Producto.descripcion.ilike(patron),
            ))
        if categoria_id:
            consulta = consulta.filter(Producto.categoria_id == categoria_id)
        return consulta.order_by(Producto.descripcion).limit(limite).all()
    finally:
        db.close()


def registrar_cancelacion_venta(usuario_id, turno_id, carrito, motivo="Cancelación manual"):
    validar_contexto_caja(usuario_id, turno_id)
    return registrar_auditoria(
        usuario_id=usuario_id,
        turno_id=turno_id,
        accion="VENTA_CANCELADA_ANTES_DE_CONFIRMAR",
        entidad="CARRITO",
        nivel="CRITICO",
        detalle={
            "motivo": motivo,
            "productos": len(carrito),
            "total": round(sum(item.get("subtotal", 0) for item in carrito), 2),
            "items": [
                {"codigo": item.get("codigo"), "cantidad": item.get("cantidad")}
                for item in carrito
            ],
        },
    )
