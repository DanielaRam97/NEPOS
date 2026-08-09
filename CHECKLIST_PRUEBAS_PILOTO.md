# Checklist de pruebas de NEPOS 0.1.0-piloto

## Instalación y arranque

- [ ] La aplicación inicia sin conexión a Internet.
- [ ] Una segunda ejecución informa que NEPOS ya está abierto.
- [ ] La migración termina en `e91b3a7c4d20`.
- [ ] Se genera un backup SQL no vacío.
- [ ] Los logs, backups y cierres aparecen en `C:\ProgramData\NEPOS`.

## Usuarios y permisos

- [ ] CAJERO no ve costos, margen, proveedor ni exportación en Productos.
- [ ] CAJERO no puede ingresar mercadería, ajustar stock ni anular ventas.
- [ ] SUPERVISOR puede realizar esas tres operaciones.
- [ ] SUPERVISOR solamente puede administrar cuentas CAJERO.
- [ ] `SOPORTE_NEPOS` no puede modificarse ni desactivarse desde la aplicación.

## Turno y caja

- [ ] El fondo inicial vacío o negativo es rechazado.
- [ ] La apertura muestra una confirmación con turno e importe.
- [ ] Otro operador no puede tomar ni cerrar el turno.
- [ ] El dueño puede suspender y recuperar una venta.
- [ ] Se puede vender dejando stock negativo y queda auditado.
- [ ] Se cobra con efectivo, QR, débito, crédito y pago combinado.
- [ ] Se prueba una venta con ticket y otra sin ticket.

## Cierre

- [ ] Se solicita el efectivo contado antes de mostrar la diferencia.
- [ ] Un sobrante o faltante exige una observación.
- [ ] El PDF y Excel incluyen esperado, contado y diferencia.
- [ ] Al cerrar se genera un backup adicional.

## Impresora y comercio

- [ ] Configuración enumera las impresoras instaladas.
- [ ] La impresión de prueba sale completa y legible.
- [ ] El ticket muestra nombre, dirección, teléfono y CUIT configurados.
- [ ] La impresora desconectada no impide guardar la venta.

## Recuperación

- [ ] Se restaura un backup en una base separada.
- [ ] Tras cortar el proceso durante una venta de prueba no queda media venta.
- [ ] Reiniciar Windows con un turno abierto permite retomarlo con su dueño.
