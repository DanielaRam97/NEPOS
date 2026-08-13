import os
import shutil
import subprocess
import tempfile
import base64
from pathlib import Path

import pymysql

from utils.rutas import ruta_configuracion


class ErrorConfiguracionInstalacion(Exception):
    pass


def buscar_mysqldump():
    configurado = (os.getenv("MYSQLDUMP_RUTA") or "").strip()
    if configurado and Path(configurado).is_file():
        return str(Path(configurado).resolve())

    encontrado = shutil.which("mysqldump")
    if encontrado:
        return str(Path(encontrado).resolve())

    if os.name != "nt":
        return ""

    candidatos = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)"):
        carpeta = os.getenv(variable)
        if not carpeta:
            continue
        raiz = Path(carpeta) / "MySQL"
        if raiz.is_dir():
            candidatos.extend(raiz.glob("**/mysqldump.exe"))

    servidores = [
        ruta for ruta in candidatos if "mysql server" in str(ruta).lower()
    ]
    elegibles = servidores or candidatos
    return str(sorted(elegibles, reverse=True)[0].resolve()) if elegibles else ""


def _texto(valor, nombre, maximo):
    valor = str(valor or "").strip()
    if not valor:
        raise ErrorConfiguracionInstalacion(f"{nombre} es obligatorio.")
    if len(valor) > maximo or "\n" in valor or "\r" in valor:
        raise ErrorConfiguracionInstalacion(f"{nombre} no es válido.")
    return valor


def normalizar_configuracion(valores):
    usuario = _texto(valores.get("db_usuario"), "El usuario MySQL", 80)
    contrasena = str(valores.get("db_contrasena") or "")
    if not contrasena:
        raise ErrorConfiguracionInstalacion(
            "La contraseña MySQL es obligatoria."
        )
    if "\n" in contrasena or "\r" in contrasena:
        raise ErrorConfiguracionInstalacion(
            "La contraseña MySQL contiene caracteres no permitidos."
        )

    host = _texto(valores.get("db_host"), "El host MySQL", 255)
    nombre = _texto(valores.get("db_nombre"), "La base de datos", 64)
    try:
        puerto = int(valores.get("db_puerto"))
        maximo_backups = int(valores.get("maximo_backups", 168))
    except (TypeError, ValueError) as error:
        raise ErrorConfiguracionInstalacion(
            "El puerto y la cantidad de backups deben ser números enteros."
        ) from error
    if not 1 <= puerto <= 65535:
        raise ErrorConfiguracionInstalacion("El puerto MySQL no es válido.")
    if not 24 <= maximo_backups <= 8760:
        raise ErrorConfiguracionInstalacion(
            "La cantidad de backups debe estar entre 24 y 8760."
        )

    mysqldump = str(valores.get("mysqldump_ruta") or "").strip()
    if not mysqldump:
        raise ErrorConfiguracionInstalacion(
            "No se encontró mysqldump. Indicá la ruta completa del ejecutable."
        )
    if not Path(mysqldump).is_file():
        raise ErrorConfiguracionInstalacion(
            "La ruta de mysqldump no existe."
        )

    return {
        "DB_USUARIO": usuario,
        "DB_CONTRASENA": contrasena,
        "DB_HOST": host,
        "DB_PUERTO": str(puerto),
        "DB_NOMBRE": nombre,
        "MYSQLDUMP_RUTA": str(Path(mysqldump).resolve()) if mysqldump else "",
        "MAXIMO_BACKUPS": str(maximo_backups),
    }


def probar_configuracion_mysql(configuracion):
    try:
        conexion = pymysql.connect(
            host=configuracion["DB_HOST"],
            port=int(configuracion["DB_PUERTO"]),
            user=configuracion["DB_USUARIO"],
            password=configuracion["DB_CONTRASENA"],
            database=configuracion["DB_NOMBRE"],
            charset="utf8mb4",
            connect_timeout=5,
        )
        conexion.close()
    except Exception as error:
        raise ErrorConfiguracionInstalacion(
            f"No se pudo conectar a MySQL: {error}"
        ) from error


def _valor_env(valor):
    texto = str(valor).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{texto}"'


def guardar_configuracion_instalacion(valores, probar_conexion=True):
    configuracion = normalizar_configuracion(valores)
    if probar_conexion:
        probar_configuracion_mysql(configuracion)

    try:
        destino = ruta_configuracion()
        destino.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ErrorConfiguracionInstalacion(
            "No se pudo preparar la carpeta compartida de NEPOS. "
            "Ejecutá el configurador como administrador."
        ) from error
    lineas = [
        "# Configuración local permanente de NEPOS.",
        "# No copiar este archivo a Git ni compartirlo.",
    ]
    for clave, valor in configuracion.items():
        if clave == "DB_CONTRASENA":
            codificada = base64.urlsafe_b64encode(
                valor.encode("utf-8")
            ).decode("ascii")
            lineas.append(f"DB_CONTRASENA_B64={codificada}")
            continue
        if valor or clave != "MYSQLDUMP_RUTA":
            lineas.append(f"{clave}={_valor_env(valor)}")
    contenido = "\n".join(lineas) + "\n"

    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix="config_",
            suffix=".tmp",
            dir=destino.parent,
            delete=False,
        ) as archivo:
            archivo.write(contenido)
            temporal = Path(archivo.name)
        os.chmod(temporal, 0o600)
        os.replace(temporal, destino)
        os.chmod(destino, 0o600)
    except OSError as error:
        if temporal:
            temporal.unlink(missing_ok=True)
        raise ErrorConfiguracionInstalacion(
            f"No se pudo guardar {destino}: {error}"
        ) from error
    for clave, valor in configuracion.items():
        os.environ[clave] = valor

    if os.name == "nt":
        resultado = subprocess.run(
            [
                "icacls",
                str(destino.parent),
                "/inheritance:e",
                "/grant:r",
                "*S-1-5-32-545:(OI)(CI)M",
                "*S-1-5-32-544:(OI)(CI)F",
                "*S-1-5-18:(OI)(CI)F",
                "/T",
                "/C",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if resultado.returncode != 0:
            raise ErrorConfiguracionInstalacion(
                "La configuración se guardó, pero Windows no permitió "
                "preparar la carpeta compartida. Ejecutá este configurador "
                "como administrador."
            )
    return destino