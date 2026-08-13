import json
from sqlalchemy.orm import joinedload
from database.conexion import nueva_sesion
from database.modelos import Turno, Usuario, VentaSuspendida


class ErrorSuspendida(Exception):
    pass


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
        db.commit()
        db.refresh(suspendida)
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
            raise ErrorSuspendida("Venta suspendida no encontrada (puede que otro cajero ya la haya recuperado).")
        _validar_operador_turno(db, suspendida.turno_id, usuario_id)
        carrito = json.loads(suspendida.datos_json)
        db.delete(suspendida)
        db.commit()
        return carrito
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def eliminar_suspendida(suspendida_id, usuario_id):
    db = nueva_sesion()
    try:
        suspendida = db.get(VentaSuspendida, suspendida_id)
        if not suspendida:
            raise ErrorSuspendida("Venta suspendida no encontrada.")
        _validar_operador_turno(db, suspendida.turno_id, usuario_id)
        db.delete(suspendida)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
