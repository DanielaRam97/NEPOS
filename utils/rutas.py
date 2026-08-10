import os
import sys
from pathlib import Path


def ejecutando_empaquetado():
    return bool(getattr(sys, "frozen", False))


def directorio_aplicacion():
    """Carpeta del ejecutable o raíz del proyecto durante el desarrollo."""
    if ejecutando_empaquetado():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def directorio_recursos():
    """Raíz de archivos empaquetados por PyInstaller."""
    temporal = getattr(sys, "_MEIPASS", None)
    if ejecutando_empaquetado() and temporal:
        return Path(temporal).resolve()
    return directorio_aplicacion()


def directorio_datos():
    configurado = os.getenv("NEPOS_DATOS_DIR")
    if configurado:
        base = Path(configurado).expanduser()
        if not base.is_absolute():
            base = directorio_aplicacion() / base
    elif os.name == "nt":
        base = Path(os.getenv("PROGRAMDATA", "C:/ProgramData")) / "NEPOS"
    else:
        base = Path.home() / ".nepos"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        raise PermissionError(
            f"No se puede escribir en {base}. Ejecutá el configurador de "
            "instalación con permisos de administrador."
        ) from error
    return base.resolve()


def ruta_configuracion():
    return directorio_datos() / "config.env"


def ruta_recurso(*partes, obligatorio=False):
    base = directorio_recursos()
    ruta = base.joinpath(*map(str, partes)).resolve()
    try:
        ruta.relative_to(base)
    except ValueError as error:
        raise ValueError("La ruta del recurso sale de la aplicación.") from error
    if obligatorio and not ruta.exists():
        relativo = Path(*map(str, partes))
        raise FileNotFoundError(
            f"No se encontró el recurso requerido: {relativo}"
        )
    return ruta


def ruta_icono(nombre, obligatorio=False):
    nombre = Path(str(nombre)).name
    return ruta_recurso(
        "assets",
        "iconos",
        nombre,
        obligatorio=obligatorio,
    )


def _crear_subdirectorio(nombre):
    ruta = directorio_datos() / nombre
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def directorio_backups():
    return _crear_subdirectorio("backups")


def directorio_cierres():
    return _crear_subdirectorio("cierres")


def directorio_logs():
    return _crear_subdirectorio("logs")


def directorio_runtime():
    return _crear_subdirectorio("runtime")