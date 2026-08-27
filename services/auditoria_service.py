import json

from database.conexion import nueva_sesion
from database.modelos import Auditoria
from datetime import datetime, time, timedelta

from sqlalchemy.orm import joinedload

def crear_registro_auditoria(
    *,
    accion,
    entidad,
    usuario_id=None,
    turno_id=None,
    venta_id=None,
    entidad_id=None,
    detalle=None,
    nivel="INFO",
):
    return Auditoria(
        usuario_id=usuario_id,
        turno_id=turno_id,
        venta_id=venta_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=json.dumps(detalle, ensure_ascii=False, default=str) if isinstance(detalle, (dict, list)) else detalle,
        nivel=nivel,
    )


def registrar_auditoria(**datos):
    db = nueva_sesion()
    try:
        registro = crear_registro_auditoria(**datos)
        db.add(registro)
        db.commit()
        return registro.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def listar_auditorias(
    fecha_desde=None,
    fecha_hasta=None,
    usuario_id=None,
    accion=None,
    turno_id=None,
    venta_id=None,
    limite=500,
):
    db = nueva_sesion()
    try:
        consulta = (
            db.query(Auditoria)
            .options(
                joinedload(Auditoria.usuario),
                joinedload(Auditoria.turno),
                joinedload(Auditoria.venta),
            )
            .order_by(Auditoria.fecha.desc())
        )

        if fecha_desde:
            inicio = datetime.combine(fecha_desde, time.min)
            consulta = consulta.filter(Auditoria.fecha >= inicio)

        if fecha_hasta:
            fin_exclusivo = datetime.combine(
                fecha_hasta + timedelta(days=1),
                time.min,
            )
            consulta = consulta.filter(Auditoria.fecha < fin_exclusivo)

        if usuario_id:
            consulta = consulta.filter(Auditoria.usuario_id == usuario_id)

        if accion:
            consulta = consulta.filter(Auditoria.accion == accion)

        if turno_id:
            consulta = consulta.filter(Auditoria.turno_id == turno_id)

        if venta_id:
            consulta = consulta.filter(Auditoria.venta_id == venta_id)

        return consulta.limit(limite).all()
    finally:
        db.close()


def listar_acciones_auditoria():
    db = nueva_sesion()
    try:
        filas = (
            db.query(Auditoria.accion)
            .distinct()
            .order_by(Auditoria.accion)
            .all()
        )
        return [accion for (accion,) in filas if accion]
    finally:
        db.close()