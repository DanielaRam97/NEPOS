import re

import bcrypt
from sqlalchemy import func, or_

from database.conexion import nueva_sesion
from database.modelos import Usuario
from services.auditoria_service import crear_registro_auditoria


ROLES_VALIDOS = ("ADMIN", "SUPERVISOR", "CAJERO")
ROLES_GESTION_USUARIOS = ("ADMIN", "SUPERVISOR")
ESTADOS_VALIDOS = ("TODOS", "ACTIVOS", "INACTIVOS")
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9._-]{3,50}$")


class ErrorUsuario(Exception):
    pass


def existen_usuarios():
    """Indica si existe una cuenta propia del comercio."""
    db = nueva_sesion()
    try:
        return (
            db.query(Usuario.id)
            .filter(Usuario.es_soporte.is_(False))
            .first()
            is not None
        )
    finally:
        db.close()


def _normalizar_usuario(valor):
    return (valor or "").strip()


def _validar_password(password):
    password = password or ""
    if len(password) < 6:
        raise ErrorUsuario(
            "La contraseña debe tener al menos 6 caracteres."
        )
    if not any(caracter.isalpha() for caracter in password):
        raise ErrorUsuario(
            "La contraseña debe contener al menos una letra."
        )
    if not any(caracter.isdigit() for caracter in password):
        raise ErrorUsuario(
            "La contraseña debe contener al menos un número."
        )


def _validar_datos(*, usuario, nombre, rol):
    usuario = _normalizar_usuario(usuario)
    nombre = (nombre or "").strip()
    rol = (rol or "").strip().upper()

    if not PATRON_USUARIO.fullmatch(usuario):
        raise ErrorUsuario(
            "El usuario debe tener entre 3 y 50 caracteres y usar "
            "solamente letras, números, punto, guion o guion bajo."
        )
    if not nombre:
        raise ErrorUsuario("El nombre es obligatorio.")
    if len(nombre) > 100:
        raise ErrorUsuario("El nombre no puede superar los 100 caracteres.")
    if rol not in ROLES_VALIDOS:
        raise ErrorUsuario("Rol inválido.")
    return usuario, nombre, rol


def _validar_gestor(db, solicitante_id):
    solicitante = db.get(Usuario, solicitante_id)
    if (
        not solicitante
        or not bool(solicitante.activo)
        or solicitante.rol not in ROLES_GESTION_USUARIOS
    ):
        raise ErrorUsuario("No tenés permiso para gestionar usuarios.")
    return solicitante


def _validar_permiso_sobre_objetivo(solicitante, objetivo):
    if bool(objetivo.protegido):
        raise ErrorUsuario(
            "La cuenta técnica de NEPOS está protegida y no se puede modificar."
        )
    if solicitante.rol == "ADMIN":
        return
    if objetivo.rol != "CAJERO":
        raise ErrorUsuario(
            "SUPERVISOR solamente puede gestionar cuentas CAJERO."
        )


def _validar_rol_asignable(solicitante, rol):
    if solicitante.rol == "SUPERVISOR" and rol != "CAJERO":
        raise ErrorUsuario(
            "SUPERVISOR solamente puede crear o editar cuentas CAJERO."
        )


def _existe_usuario(db, usuario, excluir_id=None):
    consulta = db.query(Usuario.id).filter(
        func.lower(Usuario.usuario) == usuario.casefold()
    )
    if excluir_id is not None:
        consulta = consulta.filter(Usuario.id != excluir_id)
    return consulta.first() is not None


def _cantidad_admin_activos(db):
    return (
        db.query(func.count(Usuario.id))
        .filter(
            Usuario.rol == "ADMIN",
            Usuario.activo == 1,
            Usuario.es_soporte.is_(False),
        )
        .scalar()
        or 0
    )


def listar_usuarios(
    solicitante_id,
    *,
    busqueda="",
    rol=None,
    estado="TODOS",
):
    estado = (estado or "TODOS").upper()
    if estado not in ESTADOS_VALIDOS:
        raise ErrorUsuario("Estado de filtro inválido.")
    if rol and rol not in ROLES_VALIDOS:
        raise ErrorUsuario("Rol de filtro inválido.")

    db = nueva_sesion()
    try:
        solicitante = _validar_gestor(db, solicitante_id)
        consulta = db.query(Usuario)

        # SUPERVISOR puede consultar el listado, pero las reglas de escritura
        # siguen limitándolo a las cuentas CAJERO.
        texto = (busqueda or "").strip()
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.filter(
                or_(
                    Usuario.usuario.ilike(patron),
                    Usuario.nombre.ilike(patron),
                )
            )
        if rol:
            consulta = consulta.filter(Usuario.rol == rol)
        if estado == "ACTIVOS":
            consulta = consulta.filter(Usuario.activo == 1)
        elif estado == "INACTIVOS":
            consulta = consulta.filter(Usuario.activo == 0)

        usuarios = consulta.order_by(
            Usuario.activo.desc(),
            Usuario.nombre,
        ).all()
        for usuario in usuarios:
            db.expunge(usuario)
        return usuarios
    finally:
        db.close()


def crear_usuario(
    *,
    usuario,
    nombre,
    password,
    confirmar_password=None,
    rol,
    solicitante_id=None,
):
    usuario, nombre, rol = _validar_datos(
        usuario=usuario,
        nombre=nombre,
        rol=rol,
    )
    _validar_password(password)
    if confirmar_password is not None and password != confirmar_password:
        raise ErrorUsuario("Las contraseñas no coinciden.")

    db = nueva_sesion()
    try:
        es_primer_usuario = (
            db.query(Usuario.id)
            .filter(Usuario.es_soporte.is_(False))
            .first()
            is None
        )

        if es_primer_usuario:
            if solicitante_id is not None:
                raise ErrorUsuario(
                    "La configuración inicial no admite un solicitante."
                )
            if rol != "ADMIN":
                raise ErrorUsuario(
                    "El primer usuario del sistema debe tener rol ADMIN."
                )
            solicitante = None
        else:
            if solicitante_id is None:
                raise ErrorUsuario(
                    "Un administrador o supervisor debe autorizar el alta."
                )
            solicitante = _validar_gestor(db, solicitante_id)
            _validar_rol_asignable(solicitante, rol)

        if _existe_usuario(db, usuario):
            raise ErrorUsuario("Ya existe ese nombre de usuario.")

        nuevo = Usuario(
            usuario=usuario,
            nombre=nombre,
            password_hash=bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8"),
            rol=rol,
            activo=1,
            es_soporte=False,
            protegido=False,
            creado_por_id=solicitante.id if solicitante else None,
            actualizado_por_id=solicitante.id if solicitante else None,
        )
        db.add(nuevo)
        db.flush()

        if es_primer_usuario:
            nuevo.creado_por_id = nuevo.id
            nuevo.actualizado_por_id = nuevo.id

        db.add(
            crear_registro_auditoria(
                accion="USUARIO_CREADO",
                entidad="USUARIO",
                entidad_id=nuevo.id,
                usuario_id=nuevo.id if es_primer_usuario else solicitante.id,
                detalle={
                    "usuario": nuevo.usuario,
                    "nombre": nuevo.nombre,
                    "rol": nuevo.rol,
                },
            )
        )
        db.commit()
        return nuevo.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def actualizar_usuario(
    usuario_id,
    *,
    usuario,
    nombre,
    rol,
    solicitante_id,
):
    usuario, nombre, rol = _validar_datos(
        usuario=usuario,
        nombre=nombre,
        rol=rol,
    )
    db = nueva_sesion()
    try:
        solicitante = _validar_gestor(db, solicitante_id)
        objetivo = db.get(Usuario, usuario_id)
        if not objetivo:
            raise ErrorUsuario("Usuario no encontrado.")
        _validar_permiso_sobre_objetivo(solicitante, objetivo)
        _validar_rol_asignable(solicitante, rol)

        if objetivo.id == solicitante.id and rol != objetivo.rol:
            raise ErrorUsuario("No podés cambiar tu propio rol.")
        if (
            objetivo.rol == "ADMIN"
            and rol != "ADMIN"
            and bool(objetivo.activo)
            and _cantidad_admin_activos(db) <= 1
        ):
            raise ErrorUsuario(
                "No se puede cambiar el rol del último administrador activo."
            )
        if _existe_usuario(db, usuario, excluir_id=objetivo.id):
            raise ErrorUsuario("Ya existe ese nombre de usuario.")

        anterior = {
            "usuario": objetivo.usuario,
            "nombre": objetivo.nombre,
            "rol": objetivo.rol,
        }
        objetivo.usuario = usuario
        objetivo.nombre = nombre
        objetivo.rol = rol
        objetivo.actualizado_por_id = solicitante.id

        db.add(
            crear_registro_auditoria(
                accion="USUARIO_EDITADO",
                entidad="USUARIO",
                entidad_id=objetivo.id,
                usuario_id=solicitante.id,
                detalle={
                    "anterior": anterior,
                    "nuevo": {
                        "usuario": usuario,
                        "nombre": nombre,
                        "rol": rol,
                    },
                },
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def restablecer_password(
    usuario_id,
    nueva_password,
    confirmar_password,
    solicitante_id,
):
    _validar_password(nueva_password)
    if nueva_password != confirmar_password:
        raise ErrorUsuario("Las contraseñas no coinciden.")

    db = nueva_sesion()
    try:
        solicitante = _validar_gestor(db, solicitante_id)
        objetivo = db.get(Usuario, usuario_id)
        if not objetivo:
            raise ErrorUsuario("Usuario no encontrado.")
        _validar_permiso_sobre_objetivo(solicitante, objetivo)

        objetivo.password_hash = bcrypt.hashpw(
            nueva_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        objetivo.actualizado_por_id = solicitante.id
        db.add(
            crear_registro_auditoria(
                accion="PASSWORD_RESTABLECIDA",
                entidad="USUARIO",
                entidad_id=objetivo.id,
                usuario_id=solicitante.id,
                detalle={"usuario": objetivo.usuario},
                nivel="ADVERTENCIA",
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def cambiar_estado(usuario_id, activo, solicitante_id):
    activo = bool(activo)
    db = nueva_sesion()
    try:
        solicitante = _validar_gestor(db, solicitante_id)
        objetivo = db.get(Usuario, usuario_id)
        if not objetivo:
            raise ErrorUsuario("Usuario no encontrado.")
        _validar_permiso_sobre_objetivo(solicitante, objetivo)

        if objetivo.id == solicitante.id and not activo:
            raise ErrorUsuario("No podés desactivar tu propia cuenta.")
        if (
            objetivo.rol == "ADMIN"
            and bool(objetivo.activo)
            and not activo
            and _cantidad_admin_activos(db) <= 1
        ):
            raise ErrorUsuario(
                "No se puede desactivar al último administrador activo."
            )
        if bool(objetivo.activo) == activo:
            return

        objetivo.activo = 1 if activo else 0
        objetivo.actualizado_por_id = solicitante.id
        db.add(
            crear_registro_auditoria(
                accion=("USUARIO_ACTIVADO" if activo else "USUARIO_DESACTIVADO"),
                entidad="USUARIO",
                entidad_id=objetivo.id,
                usuario_id=solicitante.id,
                detalle={
                    "usuario": objetivo.usuario,
                    "rol": objetivo.rol,
                },
                nivel="INFO" if activo else "ADVERTENCIA",
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def registrar_ultimo_acceso(usuario_id):
    """Se llama únicamente después de validar correctamente el login."""
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if usuario:
            usuario.ultimo_acceso = func.now()
            db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def recuperar_password_con_admin(
    *,
    usuario_objetivo,
    nueva_password,
    confirmar_password,
    usuario_admin,
    password_admin,
):
    usuario_objetivo = _normalizar_usuario(usuario_objetivo)
    usuario_admin = _normalizar_usuario(usuario_admin)
    _validar_password(nueva_password)
    if nueva_password != confirmar_password:
        raise ErrorUsuario("Las contraseñas nuevas no coinciden.")

    db = nueva_sesion()
    try:
        administrador = db.query(Usuario).filter(
            func.lower(Usuario.usuario) == usuario_admin.casefold()
        ).first()
        if (
            not administrador
            or not bool(administrador.activo)
            or administrador.rol != "ADMIN"
        ):
            raise ErrorUsuario("Las credenciales de administrador no son válidas.")
        try:
            correcta = bcrypt.checkpw(
                password_admin.encode("utf-8"),
                administrador.password_hash.encode("utf-8"),
            )
        except ValueError:
            correcta = False
        if not correcta:
            raise ErrorUsuario("Las credenciales de administrador no son válidas.")

        objetivo = db.query(Usuario).filter(
            func.lower(Usuario.usuario) == usuario_objetivo.casefold()
        ).first()
        if not objetivo:
            raise ErrorUsuario("El usuario que querés recuperar no existe.")
        if bool(objetivo.protegido):
            raise ErrorUsuario(
                "La cuenta técnica de NEPOS solamente se puede renovar "
                "desde el instalador local."
            )

        objetivo.password_hash = bcrypt.hashpw(
            nueva_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        objetivo.actualizado_por_id = administrador.id
        db.add(
            crear_registro_auditoria(
                accion="PASSWORD_RECUPERADA",
                entidad="USUARIO",
                entidad_id=objetivo.id,
                usuario_id=administrador.id,
                detalle={"usuario": objetivo.usuario},
                nivel="ADVERTENCIA",
            )
        )
        db.commit()
        return objetivo.usuario
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def crear_o_actualizar_usuario_soporte(
    *,
    password,
    confirmar_password,
    usuario="SOPORTE_NEPOS",
    nombre="Soporte técnico NEPOS",
):
    """Crea la cuenta técnica local sin guardar una clave universal."""
    usuario, nombre, _ = _validar_datos(
        usuario=usuario,
        nombre=nombre,
        rol="ADMIN",
    )
    _validar_password(password)
    if password != confirmar_password:
        raise ErrorUsuario("Las contraseñas no coinciden.")

    db = nueva_sesion()
    try:
        objetivo = (
            db.query(Usuario)
            .filter(Usuario.es_soporte.is_(True))
            .first()
        )
        cuenta_mismo_nombre = (
            db.query(Usuario)
            .filter(func.lower(Usuario.usuario) == usuario.casefold())
            .first()
        )
        if cuenta_mismo_nombre and cuenta_mismo_nombre is not objetivo:
            raise ErrorUsuario(
                "Ese nombre ya pertenece a una cuenta que no es de soporte."
            )

        accion = "USUARIO_SOPORTE_ACTUALIZADO"
        if objetivo is None:
            accion = "USUARIO_SOPORTE_CREADO"
            objetivo = Usuario()
            db.add(objetivo)

        objetivo.usuario = usuario
        objetivo.nombre = nombre
        objetivo.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        objetivo.rol = "ADMIN"
        objetivo.activo = 1
        objetivo.es_soporte = True
        objetivo.protegido = True
        db.flush()

        objetivo.creado_por_id = objetivo.creado_por_id or objetivo.id
        objetivo.actualizado_por_id = objetivo.id
        db.add(
            crear_registro_auditoria(
                accion=accion,
                entidad="USUARIO",
                entidad_id=objetivo.id,
                usuario_id=objetivo.id,
                detalle={"usuario": objetivo.usuario, "protegido": True},
            )
        )
        db.commit()
        return objetivo.id
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
