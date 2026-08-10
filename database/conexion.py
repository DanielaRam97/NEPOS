import os
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from utils.configuracion_entorno import cargar_entorno

cargar_entorno()

USUARIO = os.getenv("DB_USUARIO", "root")
CONTRASENA = os.getenv("DB_CONTRASENA", "")
HOST = os.getenv("DB_HOST", "127.0.0.1")
PUERTO = os.getenv("DB_PUERTO", "3306")
BASE_DATOS = os.getenv("DB_NOMBRE", "pos_db")

URL_CONEXION = URL.create(
    "mysql+pymysql",
    username=USUARIO,
    password=CONTRASENA,
    host=HOST,
    port=int(PUERTO),
    database=BASE_DATOS,
)

engine = create_engine(
    URL_CONEXION,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def nueva_sesion():
    return SessionLocal()


def probar_conexion():
    """Intenta conectar a la base de datos. Devuelve (True, None) si funciona,
    o (False, mensaje_de_error) si falla."""
    try:
        conexion = engine.connect()
        conexion.close()
        return True, None
    except Exception as e:
        return False, str(e)
