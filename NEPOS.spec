# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


RAIZ = Path(SPECPATH).resolve()
ICONO = RAIZ / "assets" / "nepos.ico"

datos = [
    (str(RAIZ / "assets"), "assets"),
    (str(RAIZ / "migrations"), "migrations"),
    (str(RAIZ / "alembic.ini"), "."),
    (str(RAIZ / "licencia.txt"), "."),
]

imports_ocultos = collect_submodules("alembic")
imports_ocultos += collect_submodules("sqlalchemy.dialects.mysql")
imports_ocultos += [
    "pymysql",
    "win32print",
]

a = Analysis(
    [str(RAIZ / "app.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    datas=datos,
    hiddenimports=imports_ocultos,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NEPOS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(ICONO) if ICONO.exists() else None,
    version=str(RAIZ / "version_info.txt"),
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="NEPOS",
)

