from sqlalchemy import func

from database.conexion import nueva_sesion
from database.modelos import GrupoPrecio, Usuario


ROLES_GESTION_GRUPOS = ("ADMIN", "SUPERVISOR")


class ErrorGrupoPrecio(Exception):
    pass


def _normalizar_nombre(nombre):
    return " ".join((nombre or "").strip().split())


def listar_grupos_precio(solo_activos=True):
    db = nueva_sesion()
    try:
        consulta = db.query(GrupoPrecio)
        if solo_activos:
            consulta = consulta.filter(GrupoPrecio.activo.is_(True))
        return consulta.order_by(GrupoPrecio.nombre).all()
    finally:
        db.close()


def crear_grupo_precio(nombre, usuario_id):
    nombre = _normalizar_nombre(nombre)
    if not nombre:
        raise ErrorGrupoPrecio(
            "El nombre del grupo de productos es obligatorio."
        )
    if len(nombre) > 100:
        raise ErrorGrupoPrecio(
            "El nombre del grupo no puede superar los 100 caracteres."
        )

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ErrorGrupoPrecio("Usuario inválido o inactivo.")
        if usuario.rol not in ROLES_GESTION_GRUPOS:
            raise ErrorGrupoPrecio(
                "Solo ADMIN o SUPERVISOR pueden crear grupos de productos."
            )

        existente = (
            db.query(GrupoPrecio)
            .filter(func.lower(GrupoPrecio.nombre) == nombre.lower())
            .first()
        )
        if existente:
            if not existente.activo:
                existente.activo = True
                db.commit()
                db.refresh(existente)
            db.expunge(existente)
            return existente

        grupo = GrupoPrecio(nombre=nombre, activo=True)
        db.add(grupo)
        db.commit()
        db.refresh(grupo)
        db.expunge(grupo)
        return grupo
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
