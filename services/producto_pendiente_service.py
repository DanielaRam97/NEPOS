from datetime import datetime

from sqlalchemy.orm import joinedload

from database.conexion import nueva_sesion
from database.modelos import Producto, Usuario
from services.auditoria_service import crear_registro_auditoria


class ErrorProductoPendiente(Exception):
    pass


def crear_producto_provisorio(
    *,
    codigo,
    descripcion,
    precio_provisorio,
    pesable,
    usuario_id,
):
    codigo = (codigo or "").strip()
    descripcion = (descripcion or "").strip()

    if not codigo:
        raise ErrorProductoPendiente("El código es obligatorio.")
    if not descripcion:
        raise ErrorProductoPendiente("La descripción es obligatoria.")
    if precio_provisorio <= 0:
        raise ErrorProductoPendiente(
            "El precio provisorio debe ser mayor que cero."
        )

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ErrorProductoPendiente("El operador no está activo.")
        if usuario.rol not in ("CAJERO", "SUPERVISOR", "ADMIN"):
            raise ErrorProductoPendiente(
                "El operador no tiene permiso para solicitar productos."
            )

        existente = (
            db.query(Producto)
            .filter(Producto.codigo == codigo)
            .first()
        )
        if existente:
            raise ErrorProductoPendiente(
                "El código ya pertenece a un producto registrado."
            )

        producto = Producto(
            codigo=codigo,
            descripcion=descripcion,
            costo=0,
            incremento=0,
            precio=round(float(precio_provisorio), 2),
            stock=0,
            iva="21%",
            pesable=bool(pesable),
            activo=1,
            pendiente_revision=True,
            solicitado_por_id=usuario_id,
            fecha_solicitud=datetime.now(),
        )
        db.add(producto)
        db.flush()
        db.add(
            crear_registro_auditoria(
                usuario_id=usuario_id,
                accion="PRODUCTO_PROVISORIO_CREADO",
                entidad="PRODUCTO",
                entidad_id=producto.id,
                nivel="CRITICO",
                detalle={
                    "codigo": producto.codigo,
                    "descripcion": producto.descripcion,
                    "precio_provisorio": producto.precio,
                },
            )
        )
        db.commit()

        return (
            db.query(Producto)
            .options(
                joinedload(Producto.categoria_rel),
                joinedload(Producto.proveedor_rel),
            )
            .filter(Producto.id == producto.id)
            .first()
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def aprobar_producto(producto_id, usuario_id):
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo or usuario.rol != "ADMIN":
            raise ErrorProductoPendiente(
                "Solo ADMIN puede aprobar productos pendientes."
            )

        producto = db.get(Producto, producto_id)
        if not producto:
            raise ErrorProductoPendiente("Producto no encontrado.")
        if not producto.pendiente_revision:
            raise ErrorProductoPendiente(
                "El producto no está pendiente de revisión."
            )
        if not producto.categoria_id:
            raise ErrorProductoPendiente(
                "Asigná una categoría antes de aprobar el producto."
            )
        if float(producto.precio or 0) <= 0:
            raise ErrorProductoPendiente(
                "El producto debe tener un precio válido."
            )

        producto.pendiente_revision = False
        db.add(
            crear_registro_auditoria(
                usuario_id=usuario_id,
                accion="PRODUCTO_PENDIENTE_APROBADO",
                entidad="PRODUCTO",
                entidad_id=producto.id,
                nivel="CRITICO",
                detalle={
                    "codigo": producto.codigo,
                    "descripcion": producto.descripcion,
                    "precio": producto.precio,
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
