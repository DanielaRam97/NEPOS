import os
from getpass import getpass

from services.configuracion_instalacion_service import (
    ErrorConfiguracionInstalacion,
    buscar_mysqldump,
    guardar_configuracion_instalacion,
)
from utils.configuracion_entorno import cargar_entorno


def _pedir(etiqueta, predeterminado):
    respuesta = input(f"{etiqueta} [{predeterminado}]: ").strip()
    return respuesta or predeterminado


def main():
    cargar_entorno()
    print("Configuración permanente de NEPOS")
    print("La contraseña no se mostrará mientras la escribís.\n")

    host = _pedir("Servidor MySQL", os.getenv("DB_HOST", "127.0.0.1"))
    puerto = _pedir("Puerto MySQL", os.getenv("DB_PUERTO", "3306"))
    base = _pedir("Base de datos", os.getenv("DB_NOMBRE", "pos_db"))
    usuario = _pedir("Usuario MySQL", os.getenv("DB_USUARIO", "nepos"))
    password = getpass("Contraseña MySQL: ")
    confirmar = getpass("Repetir contraseña MySQL: ")
    if password != confirmar:
        raise SystemExit("Las contraseñas no coinciden.")

    mysqldump_detectado = buscar_mysqldump()
    mysqldump = _pedir(
        "Ruta de mysqldump",
        mysqldump_detectado or "mysqldump",
    )
    if mysqldump == "mysqldump":
        mysqldump = buscar_mysqldump()

    backups = _pedir(
        "Cantidad máxima de backups horarios",
        os.getenv("MAXIMO_BACKUPS", "168"),
    )

    try:
        ruta = guardar_configuracion_instalacion(
            {
                "db_host": host,
                "db_puerto": puerto,
                "db_nombre": base,
                "db_usuario": usuario,
                "db_contrasena": password,
                "mysqldump_ruta": mysqldump,
                "maximo_backups": backups,
            }
        )
    except ErrorConfiguracionInstalacion as error:
        raise SystemExit(f"No se pudo guardar la configuración: {error}")

    print(f"\nConfiguración validada y guardada en:\n{ruta}")

    print("\nVerificando y actualizando la estructura de la base...")
    try:
        from services.migracion_service import (
            ErrorMigracion,
            actualizar_base_si_es_necesario,
        )

        actualizada = actualizar_base_si_es_necesario()
    except ErrorMigracion as error:
        raise SystemExit(f"No se pudieron aplicar las migraciones: {error}")
    print(
        "Migraciones aplicadas correctamente."
        if actualizada
        else "La base ya estaba actualizada."
    )

    print("\nCuenta técnica protegida: SOPORTE_NEPOS")
    soporte_password = getpass("Contraseña única de soporte: ")
    soporte_confirmar = getpass("Repetir contraseña de soporte: ")
    try:
        from services.usuario_service import (
            crear_o_actualizar_usuario_soporte,
        )

        crear_o_actualizar_usuario_soporte(
            password=soporte_password,
            confirmar_password=soporte_confirmar,
        )
    except Exception as error:
        raise SystemExit(f"No se pudo configurar SOPORTE_NEPOS: {error}")

    print("Cuenta SOPORTE_NEPOS creada o actualizada correctamente.")
    print("Guardá esa contraseña en el gestor seguro de NEPOS.")
    print("\nInstalación local configurada. Ya podés iniciar NEPOS.")


if __name__ == "__main__":
    main()