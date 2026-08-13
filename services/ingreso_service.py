from sqlalchemy.orm import joinedload

from database.conexion import nueva_sesion
from database.modelos import (
    Categoria,
    GrupoPrecio,
    Ingreso,
    MovimientoStock,
    Producto,
    Proveedor,
    Usuario,
)
from services.auditoria_service import crear_registro_auditoria
from utils.validacion import convertir_decimal_finito


ROLES_INGRESO = ("SUPERVISOR", "ADMIN")


class ErrorIngreso(Exception):
    pass


def calcular_incremento(costo, precio_venta):
    costo = float(costo or 0)
    precio_venta = float(precio_venta or 0)
    if costo <= 0:
        return 0.0
    return round((precio_venta / costo) - 1, 4)


def _validar_operador(db, usuario_id):
    usuario = db.get(Usuario, usuario_id)
    if (
        not usuario
        or not usuario.activo
        or usuario.rol not in ROLES_INGRESO
    ):
        raise ErrorIngreso(
            "El operador no tiene permiso para registrar ingresos."
        )
    return usuario


def listar_categorias():
    db = nueva_sesion()
    try:
        return db.query(Categoria).order_by(Categoria.nombre).all()
    finally:
        db.close()


def listar_proveedores():
    db = nueva_sesion()
    try:
        return db.query(Proveedor).order_by(Proveedor.nombre).all()
    finally:
        db.close()


def crear_proveedor(
    nombre,
    telefono="",
    mail="",
    direccion="",
    usuario_id=None,
):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ErrorIngreso(
            "El nombre del proveedor no puede estar vacío."
        )

    db = nueva_sesion()
    try:
        if usuario_id is not None:
            usuario = _validar_operador(db, usuario_id)
            if usuario.rol == "CAJERO":
                raise ErrorIngreso(
                    "CAJERO no puede crear proveedores."
                )
        if (
            db.query(Proveedor)
            .filter(Proveedor.nombre == nombre)
            .first()
        ):
            raise ErrorIngreso(
                "Ya existe un proveedor con ese nombre."
            )

        proveedor = Proveedor(
            nombre=nombre,
            telefono=telefono,
            mail=mail,
            direccion=direccion,
        )
        db.add(proveedor)
        db.commit()
        db.refresh(proveedor)
        return proveedor
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def buscar_producto_por_codigo(codigo):
    db = nueva_sesion()
    try:
        return (
            db.query(Producto)
            .options(
                joinedload(Producto.categoria_rel),
                joinedload(Producto.proveedor_rel),
                joinedload(Producto.grupo_precio_rel),
            )
            .filter(Producto.codigo == (codigo or "").strip())
            .first()
        )
    finally:
        db.close()


def crear_producto_nuevo(
    *,
    codigo,
    descripcion,
    categoria_id,
    proveedor_id,
    costo,
    stock_inicial,
    pesable,
    plu=None,
    precio_venta=None,
    incremento=None,
    grupo_precio_id=None,
    usuario_id=None,
):
    if precio_venta is None:
        precio_venta = float(costo) * (1 + float(incremento or 0))
    if costo < 0 or precio_venta <= 0:
        raise ErrorIngreso(
            "El costo no puede ser negativo y el precio debe ser mayor a cero."
        )

    db = nueva_sesion()
    try:
        if usuario_id is not None:
            usuario = _validar_operador(db, usuario_id)
            if usuario.rol == "CAJERO":
                raise ErrorIngreso(
                    "CAJERO debe solicitar el alta provisoria desde Caja."
                )
        if (
            db.query(Producto)
            .filter(Producto.codigo == codigo)
            .first()
        ):
            raise ErrorIngreso(
                "Ya existe un producto con ese código."
            )
        if (
            plu
            and db.query(Producto)
            .filter(Producto.plu == plu)
            .first()
        ):
            raise ErrorIngreso("Ya existe un producto con ese PLU.")

        categoria = db.get(Categoria, categoria_id)
        if not categoria:
            raise ErrorIngreso("Categoría inválida.")
        if grupo_precio_id:
            grupo = db.get(GrupoPrecio, grupo_precio_id)
            if not grupo or not grupo.activo:
                raise ErrorIngreso(
                    "Grupo de productos inválido o inactivo."
                )
        producto = Producto(
            codigo=codigo,
            plu=plu or None,
            descripcion=descripcion,
            categoria_id=categoria_id,
            proveedor_id=proveedor_id,
            costo=costo,
            incremento=calcular_incremento(costo, precio_venta),
            precio=round(float(precio_venta), 2),
            stock=stock_inicial,
            iva=categoria.iva,
            pesable=pesable,
            activo=1,
            grupo_precio_id=grupo_precio_id or None,
        )
        db.add(producto)
        db.commit()
        db.refresh(producto)
        return producto
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def registrar_ingreso_lote(
    *,
    items,
    proveedor_id=None,
    usuario_id,
):
    if not items:
        raise ErrorIngreso(
            "Agregá al menos un producto antes de guardar."
        )

    db = nueva_sesion()
    try:
        usuario = _validar_operador(db, usuario_id)
        if proveedor_id and not db.get(Proveedor, proveedor_id):
            raise ErrorIngreso("Proveedor inválido.")

        codigos = set()
        precios_por_grupo = {}
        productos_preparados = []

        for datos in items:
            codigo = (datos.get("codigo") or "").strip()
            if not codigo:
                raise ErrorIngreso(
                    "Todos los productos deben tener código."
                )
            if codigo in codigos:
                raise ErrorIngreso(
                    f"El código {codigo} está repetido en el ingreso."
                )
            codigos.add(codigo)

            try:
                cantidad = convertir_decimal_finito(
                    datos["cantidad"],
                    nombre=f"La cantidad de {codigo}",
                    minimo=0.001,
                    maximo=1000000,
                    decimales=3,
                )
                costo = convertir_decimal_finito(
                    datos["costo"],
                    nombre=f"El costo de {codigo}",
                    minimo=0.01,
                    maximo=100000000,
                    interpretar_punto_miles=True,
                )
                precio = convertir_decimal_finito(
                    datos["precio_venta"],
                    nombre=f"El precio de {codigo}",
                    minimo=0.01,
                    maximo=100000000,
                    interpretar_punto_miles=True,
                )
            except (KeyError, TypeError, ValueError) as error:
                raise ErrorIngreso(
                    str(error)
                    if isinstance(error, ValueError)
                    else f"Revisá cantidad, costo y precio del código {codigo}."
                ) from error
            if cantidad <= 0:
                raise ErrorIngreso(
                    f"La cantidad de {codigo} debe ser mayor que cero."
                )
            if costo <= 0:
                raise ErrorIngreso(
                    f"El costo de {codigo} debe ser mayor que cero."
                )
            if precio <= 0:
                raise ErrorIngreso(
                    f"El precio de venta de {codigo} debe ser mayor que cero."
                )
            if precio < costo and usuario.rol != "ADMIN":
                raise ErrorIngreso(
                    f"El precio de venta de {codigo} no puede ser menor "
                    "que su costo."
                )

            producto = (
                db.query(Producto)
                .options(joinedload(Producto.grupo_precio_rel))
                .filter(Producto.codigo == codigo)
                .with_for_update()
                .first()
            )
            if not producto:
                raise ErrorIngreso(
                    f"No existe el producto con código '{codigo}'."
                )
            grupo_id = producto.grupo_precio_id
            grupo_nombre = (
                producto.grupo_precio_rel.nombre
                if producto.grupo_precio_rel
                else ""
            )
            # Todo producto asignado a un grupo comparte costo y precio.
            # El stock se modifica únicamente para el producto ingresado.
            aplicar_grupo = grupo_id is not None
            if aplicar_grupo:
                valores_previos = precios_por_grupo.get(grupo_id)
                valores_nuevos = (costo, precio)
                if (
                    valores_previos is not None
                    and valores_previos != valores_nuevos
                ):
                    raise ErrorIngreso(
                        f"El grupo '{grupo_nombre}' tiene costos o precios "
                        "diferentes en el mismo ingreso."
                    )
                precios_por_grupo[grupo_id] = valores_nuevos

            productos_preparados.append(
                {
                    "producto": producto,
                    "cantidad": cantidad,
                    "costo": costo,
                    "precio": precio,
                    "aplicar_grupo": aplicar_grupo,
                }
            )

        propagados = set()

        detalle_auditoria = []
        for preparado in productos_preparados:
            producto = preparado["producto"]
            cantidad = preparado["cantidad"]
            costo = preparado["costo"]
            precio = preparado["precio"]
            costo_anterior = float(producto.costo or 0)
            precio_anterior = float(producto.precio or 0)
            stock_anterior = float(producto.stock or 0)
            stock_nuevo = stock_anterior + cantidad
            incremento = calcular_incremento(costo, precio)

            producto.stock = stock_nuevo
            producto.costo = costo
            producto.precio = precio
            producto.incremento = incremento
            if proveedor_id:
                producto.proveedor_id = proveedor_id

            db.add(
                Ingreso(
                    producto_id=producto.id,
                    proveedor_id=proveedor_id,
                    usuario_id=usuario_id,
                    cantidad=cantidad,
                    costo=costo,
                    incremento=incremento,
                    precio_venta=precio,
                    costo_anterior=costo_anterior,
                    precio_anterior=precio_anterior,
                )
            )
            db.add(
                MovimientoStock(
                    producto_id=producto.id,
                    usuario_id=usuario_id,
                    tipo="INGRESO",
                    cantidad=cantidad,
                    stock_anterior=stock_anterior,
                    stock_nuevo=stock_nuevo,
                    motivo="Ingreso de mercadería",
                )
            )
            detalle_auditoria.append(
                {
                    "codigo": producto.codigo,
                    "cantidad": cantidad,
                    "costo_anterior": costo_anterior,
                    "costo_nuevo": costo,
                    "precio_anterior": precio_anterior,
                    "precio_nuevo": precio,
                    "grupo_id": producto.grupo_precio_id,
                    "grupo": (
                        producto.grupo_precio_rel.nombre
                        if producto.grupo_precio_rel
                        else None
                    ),
                }
            )

        for grupo_id, valores in precios_por_grupo.items():
            costo_grupal, precio_grupal = valores
            for producto in (
                db.query(Producto)
                .filter(
                    Producto.grupo_precio_id == grupo_id,
                )
                .with_for_update()
                .all()
            ):
                costo_actual = round(float(producto.costo or 0), 2)
                precio_actual = round(float(producto.precio or 0), 2)
                if (
                    costo_actual == costo_grupal
                    and precio_actual == precio_grupal
                ):
                    continue
                producto.costo = costo_grupal
                producto.precio = precio_grupal
                producto.incremento = calcular_incremento(
                    costo_grupal,
                    precio_grupal,
                )
                propagados.add(producto.id)

        db.add(
            crear_registro_auditoria(
                usuario_id=usuario_id,
                accion="INGRESO_MERCADERIA",
                entidad="INGRESO",
                nivel="CRITICO",
                detalle={
                    "proveedor_id": proveedor_id,
                    "productos": detalle_auditoria,
                    "costos_precios_propagados": len(propagados),
                },
            )
        )
        db.commit()
        return {
            "productos": len(productos_preparados),
            # Se conserva la clave por compatibilidad con la interfaz.
            "precios_propagados": len(propagados),
            "costos_precios_propagados": len(propagados),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def registrar_ingreso(
    *,
    codigo_producto,
    cantidad,
    costo,
    proveedor_id=None,
    usuario_id,
    precio_venta=None,
    incremento=None,
):
    """Compatibilidad con llamadas anteriores de un solo producto."""
    if precio_venta is None:
        precio_venta = float(costo) * (1 + float(incremento or 0))
    resultado = registrar_ingreso_lote(
        items=[
            {
                "codigo": codigo_producto,
                "cantidad": cantidad,
                "costo": costo,
                "precio_venta": precio_venta,
                "aplicar_grupo": False,
            }
        ],
        proveedor_id=proveedor_id,
        usuario_id=usuario_id,
    )
    return resultado
