from database.conexion import nueva_sesion
from database.modelos import Turno, Usuario
from services.auditoria_service import crear_registro_auditoria
from utils.validacion import convertir_decimal_finito

FONDO_INICIAL_DEFECTO = 20000.0
FONDO_INICIAL_MAXIMO = 100000000.0


class ErrorTurno(Exception):
    pass


def obtener_turno_abierto():
    db = nueva_sesion()
    try:
        return db.query(Turno).filter(Turno.estado == "ABIERTO").first()
    finally:
        db.close()


def abrir_turno(usuario_id, nombre_turno, fondo_inicial=FONDO_INICIAL_DEFECTO):
    if nombre_turno not in ("TURNO MAÑANA", "TURNO TARDE"):
        raise ErrorTurno("Turno inválido.")

    try:
        fondo_inicial = convertir_decimal_finito(
            fondo_inicial,
            nombre="El fondo inicial",
            minimo=0,
            maximo=FONDO_INICIAL_MAXIMO,
            interpretar_punto_miles=True,
        )
    except ValueError as error:
        raise ErrorTurno(str(error)) from error

    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if (
            not usuario
            or not bool(usuario.activo)
            or usuario.rol not in ("ADMIN", "SUPERVISOR", "CAJERO")
        ):
            raise ErrorTurno("El usuario no está habilitado para abrir un turno.")
        turno_existente = db.query(Turno).filter(Turno.estado == "ABIERTO").first()
        if turno_existente:
            raise ErrorTurno(f"Ya hay un turno abierto ({turno_existente.turno}), hay que cerrarlo primero.")

        turno = Turno(
            turno=nombre_turno,
            usuario_id=usuario_id,
            fondo_inicial=fondo_inicial,
            estado="ABIERTO",
        )
        db.add(turno)
        db.flush()
        db.add(
            crear_registro_auditoria(
                accion="TURNO_ABIERTO",
                entidad="TURNO",
                entidad_id=turno.id,
                turno_id=turno.id,
                usuario_id=usuario.id,
                detalle={
                    "turno": nombre_turno,
                    "fondo_inicial": fondo_inicial,
                },
            )
        )
        db.commit()
        db.refresh(turno)
        return turno
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
