# NEPOS — Sistema de Caja

Aplicación de punto de venta de escritorio para comercios minoristas. Funciona
con PySide6, SQLAlchemy y una base MySQL 8 local, sin requerir Internet para la
operación diaria.

## Requisitos

- Windows 10/11.
- Python 3.11 o superior.
- MySQL Server 8 con tablas InnoDB.
- Impresora térmica POS-58 opcional.

## Puesta en marcha

La guía vigente está en [INSTALACION_PILOTO.md](INSTALACION_PILOTO.md). El
resumen correcto es:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python configurar_soporte_nepos.py
python app.py
```

No se deben usar `crear_tablas.py`, `schema.sql` ni `crear_usuario.py` para una
instalación nueva. Alembic es la única fuente para evolucionar el esquema y la
aplicación solicita el primer ADMIN del comercio.

## Datos y seguridad

- Las ventas se confirman dentro de transacciones MySQL.
- Las contraseñas se almacenan con bcrypt.
- La cuenta técnica `SOPORTE_NEPOS` es visible, protegida y usa una contraseña
  distinta en cada instalación.
- Los backups locales se generan al iniciar, cada hora, al cerrar turno y al
  salir de la aplicación.
- Por defecto, configuración, backups, cierres y logs se guardan en
  `C:\ProgramData\NEPOS`.

Los cambios específicos de la primera prueba están documentados en
[CAMBIOS_V0.1_PILOTO.md](CAMBIOS_V0.1_PILOTO.md).
