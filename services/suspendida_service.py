import json
from sqlalchemy.orm import joinedload
from database.conexion import nueva_sesion
from database.modelos import Turno, Usuario, VentaSuspendida
from services.auditoria_service import crear_registro_auditoria


class ErrorSuspendida(Exception):
    pass

def _detalle_carrito(carrito):
    return {
        "cantidad_items": len(carrito),
        "items": [
            {
                "codigo": item.get("codigo"),
                "descripcion": item.get("descripcion"),
                "cantidad": item.get("cantidad"),
                "subtotal": item.get(
                    "subtotal",
                    item.get("total", 0),
                ),
            }
            for item in carrito
        ],
    }

def _validar_operador_turno(db, turno_id, usuario_id):
    usuario = db.get(Usuario, usuario_id)
    turno = db.get(Turno, turno_id)
    if not usuario or not bool(usuario.activo):
        raise ErrorSuspendida("El operador no está activo.")
    if not turno or turno.estado != "ABIERTO":
        raise ErrorSuspendida("El turno ya no está abierto.")
    if turno.usuario_id != usuario.id:
        raise ErrorSuspendida(
            "Solamente el operador dueño del turno puede gestionar "
            "sus ventas suspendidas."
        )
    return usuario, turno


def suspender_venta(turno_id, usuario_id, carrito, nota=None):
    if not carrito:
        raise ErrorSuspendida("No hay nada en el carrito para suspender.")

    db = nueva_sesion()
    try:
        _validar_operador_turno(db, turno_id, usuario_id)

        suspendida = VentaSuspendida(
            turno_id=turno_id,
            usuario_id=usuario_id,
            nota=(nota or "").strip() or None,
            datos_json=json.dumps(carrito),
        )
        db.add(suspendida)
        db.flush()

        db.add(
            crear_registro_auditoria(
                accion="VENTA_SUSPENDIDA_CREADA",
                entidad="VENTA_SUSPENDIDA",
                entidad_id=suspendida.id,
                usuario_id=usuario_id,
                turno_id=turno_id,
                nivel="INFO",
                detalle={
                    "nota": suspendida.nota,
                    **_detalle_carrito(carrito),
                },
            )
        )

        db.commit()
        return suspendida.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def listar_suspendidas(turno_id, usuario_id):
    db = nueva_sesion()
    try:
        _validar_operador_turno(db, turno_id, usuario_id)
        return (
            db.query(VentaSuspendida)
            .options(joinedload(VentaSuspendida.usuario))
            .filter(VentaSuspendida.turno_id == turno_id)
            .order_by(VentaSuspendida.fecha.desc())
            .all()
        )
    finally:
        db.close()


def recuperar_suspendida(suspendida_id, usuario_id):
    db = nueva_sesion()
    try:
        suspendida = (
            db.query(VentaSuspendida)
            .filter(VentaSuspendida.id == suspendida_id)
            .with_for_update()
            .first()
        )
        if not suspendida:
            raise ErrorSuspendida(
                "Venta suspendida no encontrada "
                "(puede que otro cajero ya la haya recuperado)."
            )

        _validar_operador_turno(
            db,
            suspendida.turno_id,
            usuario_id,
        )

        carrito = json.loads(suspendida.datos_json)

        db.add(
            crear_registro_auditoria(
                accion="VENTA_SUSPENDIDA_RECUPERADA",
                entidad="VENTA_SUSPENDIDA",
                entidad_id=suspendida.id,
                usuario_id=usuario_id,
                turno_id=suspendida.turno_id,
                nivel="INFO",
                detalle={
                    "nota": suspendida.nota,
                    **_detalle_carrito(carrito),
                },
            )
        )

        db.delete(suspendida)
        db.commit()
        return carrito
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def eliminar_suspendida(suspendida_id, usuario_id, motivo):
    motivo = " ".join((motivo or "").strip().split())

    if not motivo:
        raise ErrorSuspendida(
            "Indicá el motivo por el que se descarta la venta suspendida."
        )
    if len(motivo) > 250:
        raise ErrorSuspendida(
            "El motivo no puede superar los 250 caracteres."
        )

    db = nueva_sesion()
    try:
        suspendida = (
            db.query(VentaSuspendida)
            .filter(VentaSuspendida.id == suspendida_id)
            .with_for_update()
            .first()
        )
        if not suspendida:
            raise ErrorSuspendida("Venta suspendida no encontrada.")

        _validar_operador_turno(
            db,
            suspendida.turno_id,
            usuario_id,
        )

        carrito = json.loads(suspendida.datos_json)

        db.add(
            crear_registro_auditoria(
                accion="VENTA_SUSPENDIDA_ELIMINADA",
                entidad="VENTA_SUSPENDIDA",
                entidad_id=suspendida.id,
                usuario_id=usuario_id,
                turno_id=suspendida.turno_id,
                nivel="ADVERTENCIA",
                detalle={
                    "nota": suspendida.nota,
                    "motivo_eliminacion": motivo,
                    **_detalle_carrito(carrito),
                },
            )
        )

        db.delete(suspendida)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
