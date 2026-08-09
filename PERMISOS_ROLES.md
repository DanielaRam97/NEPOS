# Permisos operativos de NEPOS

| Operación | CAJERO | SUPERVISOR | ADMIN |
|---|:---:|:---:|:---:|
| Vender en su propio turno | Sí | Sí | Sí |
| Suspender y recuperar ventas de su turno | Sí | Sí | Sí |
| Cerrar su propio turno | Sí | Sí | Sí |
| Ver catálogo sin costos internos | Sí | — | — |
| Ver costos, proveedor y margen | No | Sí | Sí |
| Importar o exportar productos | No | Sí | Sí |
| Crear/editar/desactivar productos | No | Sí | Sí |
| Ingresar mercadería | No | Sí | Sí |
| Ajustar stock | No | Sí | Sí |
| Ver historial y anular ventas | No | Sí | Sí |
| Administrar cuentas CAJERO | No | Sí | Sí |
| Administrar ADMIN/SUPERVISOR | No | No | Sí |
| Promociones, cierres y configuración | No | No | Sí |

La cuenta protegida `SOPORTE_NEPOS` conserva permisos ADMIN para intervención.
Puede entrar durante un turno ajeno para acceder a herramientas administrativas,
pero no puede vender, recuperar ventas suspendidas ni cerrar ese turno.
