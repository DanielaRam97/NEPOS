import logging
import sys
import traceback
from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from database.conexion import probar_conexion
from ui.login import VentanaLogin
from ui.apertura import VentanaApertura
from ui.caja import VentanaCaja
from ui.estilos import ESTILO_GLOBAL
from services.turno_service import obtener_turno_abierto
from backup_db import hacer_backup
from ui.configuracion_inicial import DialogoConfiguracionInicial
from services.configuracion_service import obtener_booleano, obtener_valor
from ui.primer_usuario import DialogoPrimerUsuario
from services.usuario_service import existen_usuarios
from services.migracion_service import (
    ErrorMigracion,
    actualizar_base_si_es_necesario,
)
from utils.rutas import directorio_datos, directorio_logs
from version import __version__

INTERVALO_BACKUP_HORAS = 1
logging.basicConfig(
    filename=directorio_logs() / "nepos.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("nepos")

# Referencias globales para que las ventanas no se cierren solas
ventana_login = None
ventana_apertura = None
ventana_caja = None
bloqueo_instancia = None


def manejar_excepcion(tipo, valor, traza):
    if issubclass(tipo, KeyboardInterrupt):
        sys.__excepthook__(tipo, valor, traza)
        return
    detalle = "".join(traceback.format_exception(tipo, valor, traza))
    logger.critical("Error no controlado\n%s", detalle)
    aplicacion = QApplication.instance()
    if aplicacion is not None:
        QMessageBox.critical(
            None,
            "NEPOS encontró un error",
            "La operación no pudo continuar. El detalle quedó guardado en "
            f"{directorio_logs() / 'nepos.log'}",
        )


sys.excepthook = manejar_excepcion


def mostrar_login():
    global ventana_login
    ventana_login = VentanaLogin(al_loguear_exitosamente=abrir_caja)
    ventana_login.show()


def mostrar_caja(usuario, turno):
    global ventana_caja
    ventana_caja = VentanaCaja(usuario, turno, al_cerrar_turno=mostrar_login)
    ventana_caja.showMaximized()


def abrir_caja(usuario):
    global ventana_apertura

    configuracion_incompleta = (
        not obtener_booleano("CONFIGURACION_INICIAL_COMPLETA")
        or not (obtener_valor("NOMBRE_COMERCIO") or "").strip()
    )
    if configuracion_incompleta:
        if usuario.rol != "ADMIN":
            QMessageBox.warning(
                None,
                "Configuración pendiente",
                "Un administrador debe completar la configuración inicial "
                "antes de habilitar la caja.",
            )
            mostrar_login()
            return
        asistente = DialogoConfiguracionInicial(usuario, None)
        if asistente.exec() != QDialog.DialogCode.Accepted:
            QMessageBox.information(
                None,
                "Configuración pendiente",
                "Completá la configuración inicial antes de usar la caja.",
            )
            mostrar_login()
            return

    turno_abierto = obtener_turno_abierto()
    if turno_abierto:
        es_soporte = bool(getattr(usuario, "es_soporte", False))
        if turno_abierto.usuario_id != usuario.id and not es_soporte:
            QMessageBox.warning(
                None,
                "Turno de otro operador",
                "Hay un turno abierto por otro operador. Para proteger el "
                "cierre de caja, solamente esa persona puede continuar y "
                "cerrarlo.",
            )
            mostrar_login()
            return
        mostrar_caja(usuario, turno_abierto)
    else:
        ventana_apertura = VentanaApertura(
            usuario, al_abrir_turno=lambda turno: mostrar_caja(usuario, turno)
        )
        ventana_apertura.show()

def backup_silencioso():
    """ Esta función va a ejecutar el backup sin interrumpir al usuario,
    en caso de que ocurra un error, el backup se omite solo y espera al siguiente intento"""
    try:
        hacer_backup()
    except Exception:
        logger.exception("Falló el backup automático")


app = QApplication(sys.argv)
app.setApplicationName("NEPOS")
app.setApplicationVersion(__version__)
app.setStyleSheet(ESTILO_GLOBAL)

bloqueo_instancia = QLockFile(str(directorio_datos() / "nepos.lock"))
bloqueo_instancia.setStaleLockTime(0)
if not bloqueo_instancia.tryLock(100):
    QMessageBox.warning(
        None,
        "NEPOS ya está abierto",
        "Ya existe otra instancia de NEPOS ejecutándose en esta computadora.",
    )
    sys.exit(0)

app.aboutToQuit.connect(backup_silencioso)

temporizador_backup = QTimer()
temporizador_backup.timeout.connect(backup_silencioso)
temporizador_backup.start(INTERVALO_BACKUP_HORAS * 60 * 60 * 1000)

conexion_ok, error = probar_conexion()
if not conexion_ok:
    QMessageBox.critical(
        None,
        "Error de conexión",
        "No se pudo conectar a la base de datos.\n\n"
        "Verificá que MySQL esté encendido (Servicios de Windows > MySQL80)\n"
        "y que los datos en el archivo .env sean correctos.\n\n"
        f"Detalle técnico: {error}",
    )
    sys.exit(1)

try:
    actualizar_base_si_es_necesario()
except ErrorMigracion as error:
    QMessageBox.critical(
        None,
        "No se pudo actualizar NEPOS",
        str(error),
    )
    sys.exit(1)

if not existen_usuarios():
    dialogo_inicial = DialogoPrimerUsuario(None)
    dialogo_inicial.exec()

# Backup al iniciar y luego cada hora. Una venta permanece protegida por la
# transacción de MySQL; el backup reduce la pérdida ante un daño del equipo.
QTimer.singleShot(0, backup_silencioso)
mostrar_login()
sys.exit(app.exec())
