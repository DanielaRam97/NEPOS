# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


RAIZ = Path(SPECPATH).resolve()
ICONO = RAIZ / "assets" / "nepos.ico"

datos = [
    (str(RAIZ / "migrations"), "migrations"),
    (str(RAIZ / "alembic.ini"), "."),
]

imports_ocultos = collect_submodules("alembic")
imports_ocultos += collect_submodules("sqlalchemy.dialects.mysql")
imports_ocultos += [
    "pymysql",
    "win32security",
]

a = Analysis(
    [str(RAIZ / "configurar_instalacion.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=datos,
    hiddenimports=imports_ocultos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6", "openpyxl", "reportlab"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Configurar_NEPOS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    icon=str(ICONO) if ICONO.exists() else None,
    version=str(RAIZ / "version_info.txt"),
    uac_admin=True,
)

