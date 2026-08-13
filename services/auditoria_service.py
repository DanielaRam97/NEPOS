import json

from database.conexion import nueva_sesion
from database.modelos import Auditoria


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
