from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect

from backup_db import hacer_backup
from database.conexion import engine
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


def actualizar_base_si_es_necesario():
    actuales, esperadas = estado_migraciones()
    if actuales == esperadas:
        return False
    with engine.connect() as conexion:
        hay_tablas = bool(inspect(conexion).get_table_names())
    if hay_tablas:
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