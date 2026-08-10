import os
import sys
import base64
from pathlib import Path

from dotenv import load_dotenv
from utils.rutas import directorio_aplicacion, ruta_configuracion


def cargar_entorno():
    candidatos = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(sys.executable).resolve().parent / ".env")
    else:
        candidatos.append(directorio_aplicacion() / ".env")

    vistos = set()
    for candidato in candidatos:
        candidato = candidato.resolve()
        if candidato not in vistos and candidato.is_file():
            load_dotenv(candidato, override=False)
            vistos.add(candidato)

    config_instalada = ruta_configuracion()
    if config_instalada.is_file():
        load_dotenv(config_instalada, override=True)
        password_codificada = os.getenv("DB_CONTRASENA_B64")
        if password_codificada:
            try:
                password = base64.urlsafe_b64decode(
                    password_codificada.encode("ascii")
                ).decode("utf-8")
            except Exception as error:
                raise RuntimeError(
                    f"La contraseña guardada en {config_instalada} está dañada."
                ) from error
            os.environ["DB_CONTRASENA"] = password
    return config_instalada