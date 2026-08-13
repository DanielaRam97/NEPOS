"""
Centraliza qué puede hacer cada rol. Si el día de mañana cambia una regla,
se edita acá una sola vez en vez de buscarla desnormalizada por todo el código.
"""

ADMIN = "ADMIN"
SUPERVISOR = "SUPERVISOR"
CAJERO = "CAJERO"


def puede_ajustar_stock(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_editar_productos(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_importar_productos(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_exportar_productos(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_ver_costos_productos(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_cargar_producto_nuevo(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR, CAJERO)  # el cajero lo carga, pero queda pendiente


def puede_aprobar_productos(usuario):
    return usuario.rol == ADMIN


def puede_ver_historial(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_ver_dashboard(usuario):
    return usuario.rol == ADMIN


def puede_ingreso_mercaderia(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_gestionar_usuarios(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_ver_suspendidas(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR, CAJERO)


def puede_configuracion(usuario):
    return usuario.rol == ADMIN


def puede_anular_ventas(usuario):
    return usuario.rol in (ADMIN, SUPERVISOR)


def puede_gestionar_promociones(usuario):
    return usuario.rol == ADMIN
