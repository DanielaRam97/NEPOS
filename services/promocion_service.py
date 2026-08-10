from datetime import datetime
from math import floor

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.conexion import nueva_sesion
from database.modelos import (
    GrupoPrecio,
    Producto,
    Promocion,
    PromocionItem,
    Usuario,
)


TIPOS_PROMOCION = {
    "NXM": "Lleva N y paga M (2x1, 3x2...)",
    "PORCENTAJE": "Porcentaje de descuento",
    "PRECIO_CANTIDAD": "N unidades por un precio fijo",
    "COMBO_PRECIO": "Combinar productos por un precio fijo",
    "SEGUNDA_UNIDAD": "Segunda unidad con descuento",
    "PORCENTAJE_ESCALONADO": "Porcentaje acumulativo por cantidad",
    "DESCUENTO_FIJO": "Descuento fijo por compra mínima",
}


class ErrorPromocion(Exception):
    pass


def _validar_admin(db, usuario_id):
    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.activo:
        raise ErrorPromocion("Usuario inválido o inactivo.")
    if (usuario.rol or "").upper() != "ADMIN":
        raise ErrorPromocion(
            "Solo un administrador puede gestionar promociones."
        )


def _numero(valor, nombre, *, requerido=False, minimo=None, maximo=None):
    if valor in (None, ""):
        if requerido:
            raise ErrorPromocion(f"El campo '{nombre}' es obligatorio.")
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ErrorPromocion(f"El campo '{nombre}' debe ser numérico.")
    if minimo is not None and numero < minimo:
        raise ErrorPromocion(
            f"El campo '{nombre}' debe ser mayor o igual a {minimo}."
        )
    if maximo is not None and numero > maximo:
        raise ErrorPromocion(
            f"El campo '{nombre}' debe ser menor o igual a {maximo}."
        )
    return numero


def listar_opciones_promocion():
    """Devuelve datos simples para poblar los desplegables de la interfaz."""
    db = nueva_sesion()
    try:
        productos = (
            db.query(Producto)
            .filter(Producto.activo == 1)
            .order_by(Producto.descripcion)
            .all()
        )
        grupos = (
            db.query(GrupoPrecio)
            .filter(GrupoPrecio.activo.is_(True))
            .order_by(GrupoPrecio.nombre)
            .all()
        )
        return {
            "productos": [
                {
                    "id": producto.id,
                    "codigo": producto.codigo,
                    "descripcion": producto.descripcion,
                    "precio": float(producto.precio or 0),
                    "grupo_precio_id": producto.grupo_precio_id,
                }
                for producto in productos
            ],
            "grupos": [
                {"id": grupo.id, "nombre": grupo.nombre}
                for grupo in grupos
            ],
        }
    finally:
        db.close()


def _consulta_promociones(db):
    return db.query(Promocion).options(
        joinedload(Promocion.items).joinedload(PromocionItem.producto),
        joinedload(Promocion.items).joinedload(PromocionItem.grupo_precio),
    )


def listar_promociones(solo_activas=False, vigentes=False, db=None):
    cerrar = db is None
    db = db or nueva_sesion()
    try:
        query = _consulta_promociones(db)
        if solo_activas:
            query = query.filter(Promocion.activa.is_(True))
        if vigentes:
            ahora = datetime.now()
            query = query.filter(
                or_(Promocion.fecha_desde.is_(None), Promocion.fecha_desde <= ahora),
                or_(Promocion.fecha_hasta.is_(None), Promocion.fecha_hasta >= ahora),
            )
        return query.order_by(Promocion.prioridad, Promocion.nombre).all()
    finally:
        if cerrar:
            db.close()


def _validar_items(db, items, tipo):
    if not items:
        raise ErrorPromocion(
            "Seleccioná al menos un producto o grupo de productos."
        )
    if tipo == "COMBO_PRECIO" and len(items) < 2:
        raise ErrorPromocion(
            "El combo necesita al menos dos componentes."
        )

    normalizados = []
    selectores = set()
    for item in items:
        producto_id = item.get("producto_id")
        grupo_id = item.get("grupo_precio_id")
        if bool(producto_id) == bool(grupo_id):
            raise ErrorPromocion(
                "Cada componente debe indicar un producto o un grupo, "
                "pero no ambos."
            )
        cantidad = _numero(
            item.get("cantidad", 1),
            "cantidad del componente",
            requerido=True,
            minimo=0.001,
        )
        if producto_id:
            producto = db.get(Producto, int(producto_id))
            if not producto or not producto.activo:
                raise ErrorPromocion(
                    "Uno de los productos no existe o está inactivo."
                )
            clave = ("PRODUCTO", producto.id)
            normalizados.append(
                {
                    "producto_id": producto.id,
                    "grupo_precio_id": None,
                    "cantidad": cantidad,
                }
            )
        else:
            grupo = db.get(GrupoPrecio, int(grupo_id))
            if not grupo or not grupo.activo:
                raise ErrorPromocion(
                    "Uno de los grupos no existe o está inactivo."
                )
            clave = ("GRUPO", grupo.id)
            normalizados.append(
                {
                    "producto_id": None,
                    "grupo_precio_id": grupo.id,
                    "cantidad": cantidad,
                }
            )
        if clave in selectores:
            raise ErrorPromocion(
                "No repitas el mismo producto o grupo dentro de la promoción."
            )
        selectores.add(clave)
    return normalizados


def guardar_promocion(
    *,
    nombre,
    tipo,
    items,
    usuario_id,
    promocion_id=None,
    descripcion="",
    precio_promocional=None,
    porcentaje=None,
    porcentaje_maximo=None,
    descuento_fijo=None,
    cantidad_lleva=None,
    cantidad_paga=None,
    cantidad_minima=None,
    repetible=True,
    acumulable=False,
    prioridad=100,
    fecha_desde=None,
    fecha_hasta=None,
):
    nombre = (nombre or "").strip()
    tipo = (tipo or "").strip().upper()
    if not nombre:
        raise ErrorPromocion("El nombre de la promoción es obligatorio.")
    if tipo not in TIPOS_PROMOCION:
        raise ErrorPromocion("El tipo de promoción no es válido.")
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ErrorPromocion(
            "La fecha de inicio no puede ser posterior a la fecha final."
        )

    valores = {
        "precio_promocional": _numero(
            precio_promocional, "precio promocional", minimo=0
        ),
        "porcentaje": _numero(
            porcentaje, "porcentaje", minimo=0.01, maximo=100
        ),
        "porcentaje_maximo": _numero(
            porcentaje_maximo, "porcentaje máximo", minimo=0.01, maximo=100
        ),
        "descuento_fijo": _numero(
            descuento_fijo, "descuento fijo", minimo=0.01
        ),
        "cantidad_lleva": _numero(
            cantidad_lleva, "cantidad que lleva", minimo=0.001
        ),
        "cantidad_paga": _numero(
            cantidad_paga, "cantidad que paga", minimo=0
        ),
        "cantidad_minima": _numero(
            cantidad_minima, "cantidad mínima", minimo=0.001
        ),
    }

    if tipo == "NXM":
        if valores["cantidad_lleva"] is None or valores["cantidad_paga"] is None:
            raise ErrorPromocion("Indicá cuánto lleva y cuánto paga.")
        if valores["cantidad_paga"] >= valores["cantidad_lleva"]:
            raise ErrorPromocion(
                "La cantidad que paga debe ser menor que la que lleva."
            )
    elif tipo == "PORCENTAJE":
        if valores["porcentaje"] is None:
            raise ErrorPromocion("Indicá el porcentaje de descuento.")
    elif tipo in ("PRECIO_CANTIDAD", "COMBO_PRECIO"):
        if not valores["precio_promocional"]:
            raise ErrorPromocion("Indicá el precio final de la promoción.")
        if tipo == "PRECIO_CANTIDAD" and valores["cantidad_lleva"] is None:
            raise ErrorPromocion("Indicá la cantidad incluida.")
    elif tipo == "SEGUNDA_UNIDAD":
        if valores["porcentaje"] is None:
            raise ErrorPromocion(
                "Indicá el descuento de la segunda unidad."
            )
        valores["cantidad_lleva"] = 2
    elif tipo == "PORCENTAJE_ESCALONADO":
        if valores["porcentaje"] is None or valores["cantidad_lleva"] is None:
            raise ErrorPromocion(
                "Indicá el porcentaje por escalón y la cantidad del escalón."
            )
        if valores["porcentaje_maximo"] is None:
            valores["porcentaje_maximo"] = 100
    elif tipo == "DESCUENTO_FIJO":
        if valores["descuento_fijo"] is None:
            raise ErrorPromocion("Indicá el importe del descuento.")
        if valores["cantidad_minima"] is None:
            valores["cantidad_minima"] = 1

    campos_por_tipo = {
        "NXM": {"cantidad_lleva", "cantidad_paga"},
        "PORCENTAJE": {"porcentaje", "cantidad_minima"},
        "PRECIO_CANTIDAD": {"cantidad_lleva", "precio_promocional"},
        "COMBO_PRECIO": {"precio_promocional"},
        "SEGUNDA_UNIDAD": {"cantidad_lleva", "porcentaje"},
        "PORCENTAJE_ESCALONADO": {
            "cantidad_lleva",
            "porcentaje",
            "porcentaje_maximo",
        },
        "DESCUENTO_FIJO": {"cantidad_minima", "descuento_fijo"},
    }
    utilizados = campos_por_tipo[tipo]
    valores = {
        clave: valor if clave in utilizados else None
        for clave, valor in valores.items()
    }

    db = nueva_sesion()
    try:
        _validar_admin(db, usuario_id)
        items_normalizados = _validar_items(db, items, tipo)
        consulta_duplicada = db.query(Promocion).filter(
            Promocion.nombre == nombre
        )
        if promocion_id:
            consulta_duplicada = consulta_duplicada.filter(
                Promocion.id != promocion_id
            )
        duplicada = consulta_duplicada.first()
        if duplicada:
            raise ErrorPromocion(
                "Ya existe otra promoción con ese nombre."
            )

        promocion = db.get(Promocion, promocion_id) if promocion_id else None
        if promocion_id and not promocion:
            raise ErrorPromocion("La promoción que querés editar no existe.")
        if promocion is None:
            promocion = Promocion(creado_por_id=usuario_id)
            db.add(promocion)

        promocion.nombre = nombre
        promocion.descripcion = (descripcion or "").strip() or None
        promocion.tipo = tipo
        promocion.precio_promocional = valores["precio_promocional"]
        promocion.porcentaje = valores["porcentaje"]
        promocion.porcentaje_maximo = valores["porcentaje_maximo"]
        promocion.descuento_fijo = valores["descuento_fijo"]
        promocion.cantidad_lleva = valores["cantidad_lleva"]
        promocion.cantidad_paga = valores["cantidad_paga"]
        promocion.cantidad_minima = valores["cantidad_minima"]
        promocion.repetible = bool(repetible)
        promocion.acumulable = bool(acumulable)
        promocion.prioridad = int(prioridad)
        promocion.fecha_desde = fecha_desde
        promocion.fecha_hasta = fecha_hasta

        promocion.items.clear()
        for item in items_normalizados:
            promocion.items.append(PromocionItem(**item))

        db.flush()
        identificador = promocion.id
        db.commit()
        return identificador
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def desactivar_promocion(promocion_id, usuario_id):
    db = nueva_sesion()
    try:
        _validar_admin(db, usuario_id)
        promocion = db.get(Promocion, promocion_id)
        if not promocion:
            raise ErrorPromocion("Promoción no encontrada.")
        promocion.activa = not bool(promocion.activa)
        estado = promocion.activa
        db.commit()
        return estado
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _productos_carrito(carrito, db):
    codigos = {
        str(item.get("codigo", "")).strip()
        for item in carrito
        if str(item.get("codigo", "")).strip()
    }
    productos = (
        db.query(Producto)
        .filter(Producto.codigo.in_(codigos))
        .all()
        if codigos
        else []
    )
    por_codigo = {producto.codigo: producto for producto in productos}
    resultado = {}
    for item in carrito:
        producto = por_codigo.get(str(item.get("codigo", "")).strip())
        if not producto:
            continue
        cantidad = float(item.get("cantidad", 0) or 0)
        if cantidad <= 0:
            continue
        if producto.id not in resultado:
            resultado[producto.id] = {
                "producto": producto,
                "cantidad": 0.0,
                "precio": float(producto.precio or 0),
            }
        resultado[producto.id]["cantidad"] += cantidad
    return resultado


def _ids_selector(item, productos):
    if item.producto_id:
        return {item.producto_id} if item.producto_id in productos else set()
    return {
        producto_id
        for producto_id, datos in productos.items()
        if datos["producto"].grupo_precio_id == item.grupo_precio_id
    }


def _ids_promocion(promocion, productos):
    ids = set()
    for item in promocion.items:
        ids.update(_ids_selector(item, productos))
    return ids


def _tomar_cantidad(ids, cantidad, productos, disponible, *, mayor_precio=True):
    faltante = float(cantidad)
    consumos = {}
    seleccion = []
    ordenados = sorted(
        ids,
        key=lambda producto_id: productos[producto_id]["precio"],
        reverse=mayor_precio,
    )
    for producto_id in ordenados:
        tomar = min(float(disponible.get(producto_id, 0)), faltante)
        if tomar <= 0:
            continue
        precio = productos[producto_id]["precio"]
        consumos[producto_id] = tomar
        seleccion.append((producto_id, tomar, precio))
        faltante -= tomar
        if faltante <= 0.000001:
            break
    if faltante > 0.000001:
        return None
    costo = sum(cantidad_item * precio for _, cantidad_item, precio in seleccion)
    return costo, consumos, seleccion


def _costo_mas_barato(seleccion, cantidad):
    faltante = float(cantidad)
    costo = 0.0
    for _, disponible, precio in sorted(seleccion, key=lambda dato: dato[2]):
        tomar = min(disponible, faltante)
        costo += tomar * precio
        faltante -= tomar
        if faltante <= 0.000001:
            break
    return costo


def _sumar_consumos(destino, nuevos):
    for producto_id, cantidad in nuevos.items():
        destino[producto_id] = destino.get(producto_id, 0) + cantidad


def _evaluar_combo(promocion, productos, disponible):
    trabajo = dict(disponible)
    consumos_totales = {}
    ahorro_total = 0.0
    veces = 0
    limite = 100 if promocion.repetible else 1

    while veces < limite:
        consumos_aplicacion = {}
        costo_normal = 0.0
        valido = True
        # Primero reserva productos específicos; después completa los
        # componentes por grupo. Así un grupo no consume accidentalmente
        # el único artículo requerido por otro componente del combo.
        componentes = sorted(
            promocion.items,
            key=lambda item: item.producto_id is None,
        )
        for componente in componentes:
            ids = _ids_selector(componente, productos)
            seleccion = _tomar_cantidad(
                ids,
                float(componente.cantidad),
                productos,
                trabajo,
            )
            if seleccion is None:
                valido = False
                break
            costo, consumos, _ = seleccion
            costo_normal += costo
            for producto_id, cantidad in consumos.items():
                trabajo[producto_id] -= cantidad
            _sumar_consumos(consumos_aplicacion, consumos)

        ahorro = costo_normal - float(promocion.precio_promocional or 0)
        if not valido or ahorro <= 0:
            break
        veces += 1
        ahorro_total += ahorro
        _sumar_consumos(consumos_totales, consumos_aplicacion)

    return ahorro_total, veces, consumos_totales


def _evaluar_promocion(promocion, productos, disponible):
    if promocion.tipo == "COMBO_PRECIO":
        return _evaluar_combo(promocion, productos, disponible)

    ids = _ids_promocion(promocion, productos)
    cantidad_total = sum(float(disponible.get(pid, 0)) for pid in ids)
    subtotal = sum(
        float(disponible.get(pid, 0)) * productos[pid]["precio"]
        for pid in ids
    )
    if cantidad_total <= 0:
        return 0.0, 0, {}

    tipo = promocion.tipo
    consumos = {}
    veces = 1
    ahorro = 0.0

    if tipo == "PORCENTAJE":
        minimo = float(promocion.cantidad_minima or 1)
        if cantidad_total < minimo:
            return 0.0, 0, {}
        ahorro = subtotal * float(promocion.porcentaje or 0) / 100
        consumos = {pid: float(disponible.get(pid, 0)) for pid in ids}

    elif tipo == "PORCENTAJE_ESCALONADO":
        bloque = float(promocion.cantidad_lleva or 0)
        escalones = floor(cantidad_total / bloque) if bloque > 0 else 0
        if not escalones:
            return 0.0, 0, {}
        tasa = min(
            escalones * float(promocion.porcentaje or 0),
            float(promocion.porcentaje_maximo or 100),
        )
        ahorro = subtotal * tasa / 100
        veces = escalones
        consumos = {pid: float(disponible.get(pid, 0)) for pid in ids}

    elif tipo == "DESCUENTO_FIJO":
        minimo = float(promocion.cantidad_minima or 1)
        veces = floor(cantidad_total / minimo)
        if not promocion.repetible:
            veces = min(veces, 1)
        if not veces:
            return 0.0, 0, {}
        cantidad_usada = veces * minimo
        seleccion = _tomar_cantidad(
            ids, cantidad_usada, productos, disponible
        )
        if seleccion is None:
            return 0.0, 0, {}
        costo, consumos, _ = seleccion
        ahorro = min(
            costo,
            veces * float(promocion.descuento_fijo or 0),
        )

    elif tipo in ("NXM", "PRECIO_CANTIDAD", "SEGUNDA_UNIDAD"):
        bloque = (
            2.0
            if tipo == "SEGUNDA_UNIDAD"
            else float(promocion.cantidad_lleva or 0)
        )
        veces = floor(cantidad_total / bloque) if bloque > 0 else 0
        if not promocion.repetible:
            veces = min(veces, 1)
        if not veces:
            return 0.0, 0, {}
        seleccion = _tomar_cantidad(
            ids, veces * bloque, productos, disponible
        )
        if seleccion is None:
            return 0.0, 0, {}
        costo, consumos, lotes = seleccion
        if tipo == "NXM":
            gratis = veces * (
                bloque - float(promocion.cantidad_paga or 0)
            )
            ahorro = _costo_mas_barato(lotes, gratis)
        elif tipo == "PRECIO_CANTIDAD":
            ahorro = costo - veces * float(
                promocion.precio_promocional or 0
            )
        else:
            ahorro = _costo_mas_barato(lotes, veces)
            ahorro *= float(promocion.porcentaje or 0) / 100
    else:
        return 0.0, 0, {}

    return max(ahorro, 0.0), veces, consumos


def calcular_descuento_promociones(carrito, db=None):
    """
    Calcula descuentos y devuelve ``(total, aplicaciones)``.

    Las promociones no acumulables consumen unidades en orden de prioridad.
    Las acumulables pueden superponerse, pero el descuento final nunca supera
    el subtotal del carrito.
    """
    cerrar = db is None
    db = db or nueva_sesion()
    try:
        productos = _productos_carrito(carrito, db)
        if not productos:
            return 0.0, []

        promociones = listar_promociones(
            solo_activas=True,
            vigentes=True,
            db=db,
        )
        original = {
            producto_id: datos["cantidad"]
            for producto_id, datos in productos.items()
        }
        disponible = dict(original)
        subtotal = sum(
            datos["cantidad"] * datos["precio"]
            for datos in productos.values()
        )
        descuento_total = 0.0
        aplicaciones = []

        for promocion in promociones:
            base = dict(original) if promocion.acumulable else disponible
            ahorro, veces, consumos = _evaluar_promocion(
                promocion, productos, base
            )
            ahorro = round(max(ahorro, 0), 2)
            restante = round(max(subtotal - descuento_total, 0), 2)
            ahorro = min(ahorro, restante)
            if ahorro <= 0 or veces <= 0:
                continue

            aplicaciones.append(
                {
                    "promocion_id": promocion.id,
                    "promocion": promocion.nombre,
                    "tipo": promocion.tipo,
                    "veces": veces,
                    "ahorro": ahorro,
                }
            )
            descuento_total += ahorro
            if not promocion.acumulable:
                for producto_id, cantidad in consumos.items():
                    disponible[producto_id] = max(
                        disponible.get(producto_id, 0) - cantidad,
                        0,
                    )

        return round(min(descuento_total, subtotal), 2), aplicaciones
    finally:
        if cerrar:
            db.close()
