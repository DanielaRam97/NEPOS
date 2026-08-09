from getpass import getpass

from services.usuario_service import (
    ErrorUsuario,
    crear_o_actualizar_usuario_soporte,
)


def main():
    print("Configuración de la cuenta técnica local de NEPOS")
    print("Usuario: SOPORTE_NEPOS")
    password = getpass("Contraseña única para esta instalación: ")
    confirmar = getpass("Repetir contraseña: ")
    try:
        crear_o_actualizar_usuario_soporte(
            password=password,
            confirmar_password=confirmar,
        )
    except ErrorUsuario as error:
        raise SystemExit(f"No se pudo configurar la cuenta: {error}")
    print("Cuenta de soporte creada o actualizada correctamente.")


if __name__ == "__main__":
    main()
