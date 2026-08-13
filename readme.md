NEPOS 0.1.0-piloto

Sistema de punto de venta local para Windows, PySide6 y MySQL.

Desarrollo

Requisitos:

Windows 10/11 de 64 bits.

Python 3.13 de 64 bits.

MySQL Server local.

mysqldump.exe, incluido con MySQL Server.

Desde PowerShell, en la raíz del proyecto:

py -3.13 -m venv .venv
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

La primera vez, abrí PowerShell como administrador y ejecutá:

python configurar_instalacion.py

El asistente:

guarda la conexión permanente en C:\ProgramData\NEPOS\config.env;

comprueba MySQL y mysqldump.exe;

crea un backup si la base ya contiene tablas;

aplica las migraciones de Alembic;

crea o actualiza la cuenta técnica protegida SOPORTE_NEPOS.

Después iniciá la aplicación normalmente:

python app.py

Datos locales

NEPOS utiliza estas carpetas compartidas por todos los usuarios de Windows:

C:\ProgramData\NEPOS\backups
C:\ProgramData\NEPOS\cierres
C:\ProgramData\NEPOS\config.env
C:\ProgramData\NEPOS\logs
C:\ProgramData\NEPOS\runtime

No borres esas carpetas al actualizar o desinstalar sin haber resguardado susdatos. La base de datos permanece en MySQL.

Compilar los ejecutables

La compilación debe realizarse en Windows:

.\.venv\Scripts\Activate.ps1
.\compilar.ps1

Se generan:

dist\NEPOS\NEPOS.exe
dist\Configurar_NEPOS.exe

NEPOS.exe es la aplicación diaria y no solicita permisos de administrador.Configurar_NEPOS.exe prepara o repara la instalación y sí solicita elevación.

Crear el instalador

Instalá Inno Setup 6 y volvé a ejecutar:

.\compilar.ps1

Si el compilador de Inno Setup está instalado en su ruta habitual, también segenera:

dist\instalador\NEPOS_Setup_0.1.0-piloto.exe

El instalador ejecuta obligatoriamente Configurar_NEPOS.exe antes de ofrecerel inicio de NEPOS. MySQL Server es un requisito externo y no se incluye.

Verificaciones antes de publicar

python -m compileall app.py database services ui utils
alembic heads
alembic current

Debe existir una sola cabeza de Alembic: f2d6a8b13c40.

Consultá también:

CHECKLIST_PRUEBAS_PILOTO.md

INSTALACION_PILOTO.md

PERMISOS_ROLES.md