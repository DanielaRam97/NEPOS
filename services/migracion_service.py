from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from backup_db import hacer_backup
from database import modelos as _modelos  # Registra todas las tablas en Base.
from database.conexion import Base, engine
from utils.rutas import ruta_recurso


class ErrorMigracion(Exception):
    pass


def _configuracion_alembic():
    try:
        archivo = ruta_recurso("alembic.ini", obligatorio=True)
        migraciones = ruta_recurso("migrations", obligatorio=True)
    except FileNotFoundError as error:
        raise ErrorMigracion(
            "La instalación no contiene los recursos de migración. "
            "Reinstalá NEPOS con el paquete completo."
        ) from error
    config = Config(str(archivo))
    config.set_main_option(
        "script_location",
        str(migraciones),
    )
    return config


def estado_migraciones():
    config = _configuracion_alembic()
    scripts = ScriptDirectory.from_config(config)
    heads_esperadas = set(scripts.get_heads())
    with engine.connect() as conexion:
        heads_actuales = set(
            MigrationContext.configure(conexion).get_current_heads()
        )
    return heads_actuales, heads_esperadas


def _tablas_de_negocio():
    with engine.connect() as conexion:
        return set(inspect(conexion).get_table_names()) - {"alembic_version"}


def _inicializar_base_vacia():
    """Crea el esquema actual cuando la instalación no tiene tablas.

    La primera revisión histórica de este proyecto representa una base que ya
    existía y no contiene los CREATE TABLE. Por eso una instalación nueva debe
    construirse desde los modelos actuales y quedar estampada directamente en
    la cabeza vigente. Las bases con tablas continúan por el flujo normal de
    migraciones y backup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        command.stamp(_configuracion_alembic(), "head", purge=True)
    except Exception as error:
        raise ErrorMigracion(
            f"No se pudo inicializar la base de datos vacía: {error}"
        ) from error

    actuales, esperadas = estado_migraciones()
    if actuales != esperadas:
        raise ErrorMigracion(
            "La base nueva se creó, pero no quedó en la revisión esperada."
        )
    return True


def actualizar_base_si_es_necesario():
    actuales, esperadas = estado_migraciones()
    if actuales == esperadas:
        return False

    tablas_de_negocio = _tablas_de_negocio()
    if not tablas_de_negocio:
        return _inicializar_base_vacia()

    if tablas_de_negocio:
        try:
            hacer_backup()
        except Exception as error:
            raise ErrorMigracion(
                "Hay una actualización pendiente, pero no se pudo crear "
                f"el backup previo: {error}"
            ) from error
    try:
        command.upgrade(_configuracion_alembic(), "head")
    except Exception as error:
        raise ErrorMigracion(
            f"No se pudo actualizar la base de datos: {error}"
        ) from error
    actuales, esperadas = estado_migraciones()
    if actuales != esperadas:
        raise ErrorMigracion(
            "La base no quedó en la revisión esperada después de actualizar."
        )
    return True