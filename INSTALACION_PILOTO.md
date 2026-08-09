# NEPOS — instalación piloto local

Esta versión funciona sin Internet y utiliza MySQL en la misma computadora.

## Instalación

1. Instalar Python 3.11 o superior y MySQL 8 en la PC del comercio.
2. Crear la base `pos_db` y un usuario MySQL exclusivo para NEPOS.
3. Copiar `.env.example` como `.env` y completar la contraseña local.
4. Crear y activar el entorno virtual e instalar las dependencias:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

5. Aplicar todas las migraciones:

   ```powershell
   alembic upgrade head
   alembic heads
   ```

   `alembic heads` debe mostrar solamente `e91b3a7c4d20 (head)`.

6. Crear la cuenta técnica protegida de NEPOS:

   ```powershell
   python configurar_soporte_nepos.py
   ```

   Usar una contraseña fuerte y única para esa instalación. Guardarla en el
   gestor seguro de credenciales de NEPOS; no escribirla en el código ni en
   `.env`.

7. Iniciar la aplicación con `python app.py` y crear el primer ADMIN propio
   del comercio cuando el sistema lo solicite.

## Comprobaciones antes de vender

- Registrar una venta en efectivo y verificar total, stock y vuelto.
- Registrar una venta que deje stock negativo y verificar que sea aceptada.
- Cobrar una vez con ticket y otra vez desmarcando la impresión.
- Confirmar que solamente ADMIN o SUPERVISOR puedan anular y ajustar stock.
- Confirmar que otro usuario no pueda tomar ni cerrar el turno abierto.
- Confirmar que `SOPORTE_NEPOS` pueda entrar para intervenir, pero no vender ni
  cerrar el turno de otro operador.
- Abrir un backup SQL y comprobar que no esté vacío.
- Hacer una restauración de prueba en una base separada.
- Desconectar Internet y repetir una venta completa.
- Configurar correctamente la impresora POS-58 y hacer una prueba física.
- Abrir un turno con fondo cero y comprobar que un fondo negativo sea rechazado.
- Verificar que CAJERO no vea costos, margen, proveedor ni exportación de productos.
- Cerrar el turno ingresando efectivo contado y verificar la diferencia de caja.

## Datos locales

Por defecto se guardan en `C:\ProgramData\NEPOS`:

- `backups`: copia SQL al iniciar, cada hora, al cerrar el turno y al salir.
- `cierres`: reportes PDF y Excel de cada cierre.
- `logs`: errores de operación y de backups.

La ubicación puede cambiarse mediante `NEPOS_DATOS_DIR` en `.env`.

## Alcance y advertencias del piloto

- La venta y el descuento de stock se confirman en una única transacción de
  MySQL. Un corte en medio de esa operación no debe dejar media venta grabada.
- El backup horario no reemplaza un UPS: todavía puede perderse información
  posterior al último backup si falla físicamente el disco o la base.
- Los backups están en la misma PC durante este piloto. Deben copiarse
  manualmente a otro dispositivo con frecuencia hasta incorporar la nube.
- No compartir la cuenta `SOPORTE_NEPOS` con el comercio ni usar una contraseña
  repetida entre instalaciones.
