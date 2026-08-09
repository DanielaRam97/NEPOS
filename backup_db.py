"""
Genera un backup de la base de datos MySQL usando mysqldump, y borra
automáticamente los backups más viejos para no llenar el disco.

Uso manual: python backup_db.py
Uso automático: al iniciar, cada hora y al cerrar NEPOS.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path
from utils.rutas import directorio_backups
from utils.configuracion_entorno import cargar_entorno

cargar_entorno()

MAXIMO_BACKUPS = int(os.getenv("MAXIMO_BACKUPS", "168"))


def hacer_backup():
    usuario = os.getenv("DB_USUARIO", "root")
    contrasena = os.getenv("DB_CONTRASENA", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    puerto = os.getenv("DB_PUERTO", "3306")
    nombre_bd = os.getenv("DB_NOMBRE", "pos_db")

    carpeta_backups = directorio_backups()

    marca_tiempo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    archivo_salida = carpeta_backups / f"backup_{nombre_bd}_{marca_tiempo}.sql"

    comando = [
        os.getenv("MYSQLDUMP_RUTA", "mysqldump"),
        f"-u{usuario}",
        f"-h{host}",
        f"-P{puerto}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--events",
        "--default-character-set=utf8mb4",
        nombre_bd,
    ]

    entorno = os.environ.copy()
    entorno["MYSQL_PWD"] = contrasena
    try:
        with archivo_salida.open("w", encoding="utf-8") as archivo:
            resultado = subprocess.run(
                comando,
                stdout=archivo,
                stderr=subprocess.PIPE,
                env=entorno,
                check=False,
            )
    except OSError as error:
        archivo_salida.unlink(missing_ok=True)
        raise RuntimeError(
            "No se pudo ejecutar mysqldump. Revisá MYSQLDUMP_RUTA. "
            f"Detalle: {error}"
        ) from error

    if resultado.returncode != 0:
        archivo_salida.unlink(missing_ok=True)
        error = resultado.stderr.decode(errors="replace")
        raise RuntimeError(f"mysqldump falló: {error}")

    _limpiar_backups_viejos(carpeta_backups)
    return str(archivo_salida)


def _limpiar_backups_viejos(carpeta_backups=None):
    carpeta_backups = Path(carpeta_backups or directorio_backups())
    archivos = sorted(
        (
            ruta
            for ruta in carpeta_backups.iterdir()
            if ruta.name.startswith("backup_") and ruta.suffix == ".sql"
        ),
        reverse=True,
    )
    for viejo in archivos[MAXIMO_BACKUPS:]:
        viejo.unlink()


if __name__ == "__main__":
    ruta = hacer_backup()
    print(f"Backup creado correctamente: {ruta}")
