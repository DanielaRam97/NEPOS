# Cambios de cierre para la versión piloto

- Habilita ventas con stock negativo y registra una advertencia de auditoría.
- Pregunta en el cobro si se debe imprimir el ticket.
- Permite anular ventas y ajustar stock a ADMIN y SUPERVISOR, con validación
  también en los servicios.
- Restringe el turno abierto y su cierre al operador que lo abrió.
- Agrega cuenta técnica NEPOS protegida, visible y con contraseña única por PC.
- Permite que soporte acceda a las herramientas de intervención durante un
  turno ajeno, sin autorizarle ventas ni el cierre de ese turno.
- Mantiene separado el primer ADMIN propio del comercio.
- Ejecuta backups locales al iniciar, cada hora, al cerrar turno y al salir.
- Guarda backups, cierres y logs bajo el directorio local de datos de NEPOS.
- Mantiene una sola cabeza de migraciones después de las ramas de promociones
  y auditoría de usuarios.
- Rechaza fondos iniciales negativos, infinitos o fuera de rango.
- Incorpora arqueo de cierre con efectivo contado, diferencia y observación.
- Oculta costos, proveedor, margen y exportación de productos al rol CAJERO.
- Permite al dueño del turno recuperar sus propias ventas suspendidas.
- Valida en servicios los permisos de ingresos, ajustes y ventas suspendidas.
- Permite configurar los datos del comercio y seleccionar/probar la impresora.
- Prepara rutas de recursos y datos para una futura compilación con PyInstaller.
- Evita dos instancias simultáneas y aplica migraciones con backup previo.
# IVA por venta y por turno

- Carnicería y Panadería se registran automáticamente con IVA 10,5%.
- Las demás categorías se registran con IVA 21%.
- Cada detalle de venta conserva la alícuota utilizada, aunque luego cambie el producto.
- Al cerrar el turno se guardan por separado los importes de IVA 10,5% e IVA 21%.
- Los reportes de cierres, Excel y PDF muestran ambos importes.
- Si no hay impresora configurada, el cobro queda habilitado y la opción de ticket aparece desactivada.
