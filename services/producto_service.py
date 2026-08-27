from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, selectinload

from database.conexion import nueva_sesion
from database.modelos import (
    Categoria,
    GrupoPrecio,
    Producto,
    Proveedor,
    Usuario,
)
from services.auditoria_service import crear_registro_auditoria

from utils.validacion import convertir_decimal_finito


ROLES_GESTION_PRODUCTOS = ("ADMIN", "SUPERVISOR")


class ErrorProducto(Exception):
    pass


def listar_productos(busqueda="", categoria_id=None, estado="TODOS"):
    db = nueva_sesion()
    try:
        query = (
            db.query(Producto)
            .options(
                joinedload(Producto.categoria_rel),
                joinedload(Producto.proveedor_rel),
                selectinload(Producto.grupo_precio_rel),
            )
            .order_by(Producto.descripcion)
        )

        busqueda = (busqueda or "").strip()
        if busqueda:
            patron = f"%{busqueda}%"
            query = query.filter(
                or_(
                    Producto.codigo.ilike(patron),
                    Producto.descripcion.ilike(patron),
                    Producto.plu.ilike(patron),
                )
            )

        if categoria_id:
            query = query.filter(Producto.categoria_id == categoria_id)

        if estado == "ACTIVOS":
            query = query.filter(Producto.activo == 1)
        elif estado == "INACTIVOS":
            query = query.filter(Producto.activo == 0)

        productos = query.all()
        for producto in productos:
            producto.grupo_precio_nombre = (
                producto.grupo_precio_rel.nombre
                if producto.grupo_precio_rel
                else ""
            )
        return productos
    finally:
        db.close()


def listar_categorias():
    db = nueva_sesion()
    try:
        return db.query(Categoria).order_by(Categoria.nombre).all()
    finally:
        db.close()


def crear_categoria(nombre, iva, usuario_id):
    nombre = " ".join((nombre or "").strip().split())
    if not nombre:
        raise ErrorProducto("El nombre de la categoría es obligatorio.")
    if len(nombre) > 80:
        raise ErrorProducto(
            "El nombre de la categoría no puede superar los 80 caracteres."
        )

    try:
        iva_numero = float(iva)
    except (TypeError, ValueError) as error:
        raise ErrorProducto("La alícuota de IVA es inválida.") from error

    if abs(iva_numero - 10.5) < 0.01:
        iva_formateado = "10.5%"
    elif abs(iva_numero - 21.0) < 0.01:
        iva_formateado = "21%"
    else:
        raise ErrorProducto("El IVA debe ser 10,5% o 21%.")

    db = nueva_sesion()
    try:
        _validar_permiso(db, usuario_id)
        existente = (
            db.query(Categoria)
            .filter(func.lower(Categoria.nombre) == nombre.lower())
            .first()
        )
        if existente:
            raise ErrorProducto(
                f"Ya existe la categoría '{existente.nombre}'."
            )

        categoria = Categoria(
            nombre=nombre,
            iva=iva_formateado,
        )
        db.add(categoria)
        db.flush()

        db.add(
            crear_registro_auditoria(
                accion="CREAR_CATEGORIA",
                entidad="CATEGORIA",
                entidad_id=categoria.id,
                usuario_id=usuario_id,
                detalle={
                    "nombre": categoria.nombre,
                    "iva": categoria.iva,
                },
            )
        )

        db.commit()
        db.refresh(categoria)
        db.expunge(categoria)
        return categoria
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def listar_proveedores():
    db = nueva_sesion()
    try:
        return db.query(Proveedor).order_by(Proveedor.nombre).all()
    finally:
        db.close()


def _validar_permiso(db, usuario_id):
    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.activo:
        raise ErrorProducto("Usuario inválido o inactivo.")
    if usuario.rol not in ROLES_GESTION_PRODUCTOS:
        raise ErrorProducto("No tenés permiso para modificar productos.")
    return usuario


def crear_producto(
    *, usuario_id, codigo, descripcion, plu, categoria_id,
    proveedor_id, costo, precio, grupo_precio_id, pesable,
):
    codigo = (codigo or "").strip()
    descripcion = (descripcion or "").strip()
    plu = (plu or "").strip() or None

    if not codigo:
        raise ErrorProducto("El código es obligatorio.")
    if not descripcion:
        raise ErrorProducto("La descripción es obligatoria.")
    try:
        costo = convertir_decimal_finito(
            costo,
            nombre="El costo",
            minimo=0,
            maximo=100000000,
            interpretar_punto_miles=True,
        )
        precio = convertir_decimal_finito(
            precio,
            nombre="El precio de venta",
            minimo=0.01,
            maximo=100000000,
            interpretar_punto_miles=True,
        )
    except ValueError as error:
        raise ErrorProducto(str(error)) from error

    db = nueva_sesion()
    try:
        usuario = _validar_permiso(db, usuario_id)
        if db.query(Producto).filter(Producto.codigo == codigo).first():
            raise ErrorProducto("Ya existe un producto con ese código.")
        if plu and db.query(Producto).filter(Producto.plu == plu).first():
            raise ErrorProducto("Ya existe un producto con ese PLU.")

        categoria = db.get(Categoria, categoria_id)
        if not categoria:
            raise ErrorProducto("Seleccioná o creá una categoría.")
        if proveedor_id and not db.get(Proveedor, proveedor_id):
            raise ErrorProducto("Proveedor inválido.")
        if grupo_precio_id:
            grupo = db.get(GrupoPrecio, grupo_precio_id)
            if not grupo or not grupo.activo:
                raise ErrorProducto("Grupo de productos inválido o inactivo.")
        if precio < costo and usuario.rol != "ADMIN":
            raise ErrorProducto(
                "El precio de venta no puede ser menor que el costo."
            )

        producto = Producto(
            codigo=codigo,
            descripcion=descripcion,
            plu=plu,
            categoria_id=categoria_id,
            proveedor_id=proveedor_id or None,
            costo=round(float(costo), 2),
            precio=round(float(precio), 2),
            incremento=(
                round((float(precio) / float(costo)) - 1, 4)
                if costo > 0 else 0
            ),
            stock=0,
            iva=categoria.iva,
            pesable=bool(pesable),
            activo=1,
            grupo_precio_id=grupo_precio_id or None,
            pendiente_revision=False,
        )
        db.add(producto)
        db.commit()
        return producto.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def actualizar_producto(
    *, producto_id, usuario_id, codigo, descripcion, plu, categoria_id,
    proveedor_id, costo, precio, grupo_precio_id, pesable,
    aplicar_precio_grupo=False,
):
    codigo = (codigo or "").strip()
    descripcion = (descripcion or "").strip()
    plu = (plu or "").strip() or None

    if not codigo:
        raise ErrorProducto("El código es obligatorio.")
    if not descripcion:
        raise ErrorProducto("La descripción es obligatoria.")
    try:
        costo = convertir_decimal_finito(
            costo,
            nombre="El costo",
            minimo=0,
            maximo=100000000,
            interpretar_punto_miles=True,
        )
        precio = convertir_decimal_finito(
            precio,
            nombre="El precio de venta",
            minimo=0.01,
            maximo=100000000,
            interpretar_punto_miles=True,
        )
    except ValueError as error:
        raise ErrorProducto(str(error)) from error

    db = nueva_sesion()
    try:
        usuario = _validar_permiso(db, usuario_id)
        producto = db.get(Producto, producto_id)
        if not producto:
            raise ErrorProducto("Producto no encontrado.")

        codigo_repetido = (
            db.query(Producto)
            .filter(Producto.codigo == codigo, Producto.id != producto_id)
            .first()
        )
        if codigo_repetido:
            raise ErrorProducto("Ya existe otro producto con ese código.")

        if plu:
            plu_repetido = (
                db.query(Producto)
                .filter(Producto.plu == plu, Producto.id != producto_id)
                .first()
            )
            if plu_repetido:
                raise ErrorProducto("Ya existe otro producto con ese PLU.")

        categoria = db.get(Categoria, categoria_id)
        if not categoria:
            raise ErrorProducto("Seleccioná o creá una categoría.")
        if proveedor_id and not db.get(Proveedor, proveedor_id):
            raise ErrorProducto("Proveedor inválido.")
        if grupo_precio_id:
            grupo = db.get(GrupoPrecio, grupo_precio_id)
            if not grupo or not grupo.activo:
                raise ErrorProducto("Grupo de productos inválido o inactivo.")
        elif aplicar_precio_grupo:
            raise ErrorProducto(
                "Seleccioná un grupo antes de aplicar el precio grupal."
            )
        if precio < costo and usuario.rol != "ADMIN":
            raise ErrorProducto(
                "El precio de venta no puede ser menor que el costo."
            )

        producto.codigo = codigo
        producto.descripcion = descripcion
        producto.plu = plu
        producto.categoria_id = categoria_id
        producto.proveedor_id = proveedor_id or None
        producto.costo = costo
        producto.precio = round(precio, 2)
        producto.incremento = (
            round((precio / costo) - 1, 4)
            if costo > 0
            else 0
        )
        producto.grupo_precio_id = grupo_precio_id or None
        producto.iva = categoria.iva
        producto.pesable = bool(pesable)

        productos_grupo_actualizados = 0
        if aplicar_precio_grupo:
            productos_grupo = (
                db.query(Producto)
                .filter(
                    Producto.grupo_precio_id == grupo_precio_id,
                    Producto.activo == 1,
                )
                .with_for_update()
                .all()
            )
            if usuario.rol != "ADMIN":
                productos_bajo_costo = [
                    miembro.descripcion
                    for miembro in productos_grupo
                    if float(miembro.costo or 0) > precio
                ]
                if productos_bajo_costo:
                    raise ErrorProducto(
                        "El precio grupal queda por debajo del costo de: "
                        + ", ".join(productos_bajo_costo[:4])
                    )

            precio_grupal = round(float(precio), 2)
            for miembro in productos_grupo:
                costo_miembro = float(miembro.costo or 0)
                miembro.precio = precio_grupal
                miembro.incremento = (
                    round((precio_grupal / costo_miembro) - 1, 4)
                    if costo_miembro > 0
                    else 0
                )
            productos_grupo_actualizados = len(productos_grupo)

        db.commit()
        return {
            "productos_grupo_actualizados": (
                productos_grupo_actualizados
            ),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def cambiar_estado_producto(producto_id, activo, usuario_id):
    db = nueva_sesion()
    try:
        usuario = _validar_permiso(db, usuario_id)
        producto = db.get(Producto, producto_id)
        if not producto:
            raise ErrorProducto("Producto no encontrado.")
        if producto.pendiente_revision and usuario.rol != "ADMIN":
            raise ErrorProducto(
                "Solo ADMIN puede activar o desactivar un producto pendiente."
            )

        producto.activo = 1 if activo else 0
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()