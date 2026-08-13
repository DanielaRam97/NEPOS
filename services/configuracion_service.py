import re

from database.conexion import nueva_sesion
from database.modelos import ConfiguracionSistema, Usuario
from services.auditoria_service import crear_registro_auditoria


VALORES_DEFAULT = {
    "RECARGO_CIGARRILLOS": "0.15",
    "RECARGO_CREDITO": "0.15",
    "REDONDEO_DECIMALES": "2",
    "IVA_DEFAULT": "21",
    "MEDIOS_PAGO": "EFECTIVO,QR,DEBITO,CREDITO",
    "PERMITIR_STOCK_NEGATIVO": "true",
    "NOMBRE_COMERCIO": "",
    "DIRECCION_COMERCIO": "",
    "TELEFONO_COMERCIO": "",
    "CUIT_COMERCIO": "",
    "NOMBRE_IMPRESORA": "",
}


def obtener_valor(clave, db=None):
    cerrar = db is None
    db = db or nueva_sesion()
    try:
        configuracion = db.get(ConfiguracionSistema, clave)
        return configuracion.valor if configuracion else VALORES_DEFAULT.get(clave)
    finally:
        if cerrar:
            db.close()


def obtener_decimal(clave, db=None):
    return float(obtener_valor(clave, db) or 0)


def obtener_entero(clave, db=None):
    return int(obtener_valor(clave, db) or 0)


def obtener_booleano(clave, db=None):
    return str(obtener_valor(clave, db)).strip().lower() in ("1", "true", "si", "sí")


def obtener_lista(clave, db=None):
    return [
        valor.strip()
        for valor in str(obtener_valor(clave, db) or "").split(",")
        if valor.strip()
    ]


def redondear_importe(valor, db=None):
    return round(float(valor), obtener_entero("REDONDEO_DECIMALES", db))


def actualizar_valor(clave, valor, usuario_id):
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo or usuario.rol != "ADMIN":
            raise PermissionError(
                "Solo un usuario ADMIN puede modificar la configuración."
            )
        configuracion = db.get(ConfiguracionSistema, clave)
        if not configuracion:
            configuracion = ConfiguracionSistema(clave=clave, valor=str(valor))
            db.add(configuracion)
        configuracion.valor = str(valor)
        configuracion.actualizado_por_id = usuario.id
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def obtener_configuracion_caja():
    return {
        "recargo_cigarrillos": obtener_decimal("RECARGO_CIGARRILLOS"),
        "recargo_credito": obtener_decimal("RECARGO_CREDITO"),
        "redondeo_decimales": obtener_entero("REDONDEO_DECIMALES"),
        "iva_default": obtener_decimal("IVA_DEFAULT"),
        "medios_pago": obtener_lista("MEDIOS_PAGO"),
        "permitir_stock_negativo": obtener_booleano("PERMITIR_STOCK_NEGATIVO"),
    }


def obtener_configuracion_comercio():
    db = nueva_sesion()
    try:
        return {
            "nombre": obtener_valor("NOMBRE_COMERCIO", db) or "NEPOS",
            "direccion": obtener_valor("DIRECCION_COMERCIO", db) or "",
            "telefono": obtener_valor("TELEFONO_COMERCIO", db) or "",
            "cuit": obtener_valor("CUIT_COMERCIO", db) or "",
            "impresora": obtener_valor("NOMBRE_IMPRESORA", db) or "",
        }
    finally:
        db.close()


def _normalizar_cuit(valor):
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return ""
    if len(digitos) != 11:
        raise ValueError("El CUIT debe tener 11 dígitos.")
    pesos = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    verificador = 11 - sum(
        int(digito) * peso
        for digito, peso in zip(digitos[:10], pesos)
    ) % 11
    verificador = 0 if verificador == 11 else 9 if verificador == 10 else verificador
    if verificador != int(digitos[-1]):
        raise ValueError("El CUIT ingresado no es válido.")
    return f"{digitos[:2]}-{digitos[2:10]}-{digitos[10]}"


def actualizar_configuracion_comercio(valores, usuario_id):
    nombre = " ".join((valores.get("nombre") or "").strip().split())
    direccion = " ".join((valores.get("direccion") or "").strip().split())
    telefono = " ".join((valores.get("telefono") or "").strip().split())
    impresora = (valores.get("impresora") or "").strip()
    if not nombre:
        raise ValueError("El nombre del comercio es obligatorio.")
    if len(nombre) > 120:
        raise ValueError("El nombre del comercio no puede superar 120 caracteres.")
    if len(direccion) > 180 or len(telefono) > 50 or len(impresora) > 255:
        raise ValueError("Revisá la longitud de los datos del comercio.")
    cuit = _normalizar_cuit(valores.get("cuit"))

    nuevos_valores = {
        "NOMBRE_COMERCIO": nombre,
        "DIRECCION_COMERCIO": direccion,
        "TELEFONO_COMERCIO": telefono,
        "CUIT_COMERCIO": cuit,
        "NOMBRE_IMPRESORA": impresora,
    }
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo or usuario.rol != "ADMIN":
            raise PermissionError(
                "Solo un usuario ADMIN puede modificar los datos del comercio."
            )
        for clave, valor in nuevos_valores.items():
            configuracion = db.get(ConfiguracionSistema, clave)
            if not configuracion:
                configuracion = ConfiguracionSistema(clave=clave, valor=valor)
                db.add(configuracion)
            configuracion.valor = valor
            configuracion.actualizado_por_id = usuario.id
        db.add(
            crear_registro_auditoria(
                usuario_id=usuario.id,
                accion="CONFIGURACION_COMERCIO_MODIFICADA",
                entidad="CONFIGURACION_SISTEMA",
                detalle={
                    "nombre": nombre,
                    "direccion": direccion,
                    "telefono": telefono,
                    "cuit": cuit,
                    "impresora": impresora,
                },
                nivel="CRITICO",
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def actualizar_configuracion_caja(valores, usuario_id):
    db = nueva_sesion()
    try:
        usuario = db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo or usuario.rol != "ADMIN":
            raise PermissionError("Solo un usuario ADMIN puede modificar la configuración de Caja.")

        recargo_cigarrillos = float(valores["recargo_cigarrillos"])
        recargo_credito = float(valores["recargo_credito"])
        redondeo = int(valores["redondeo_decimales"])
        iva_default = float(valores["iva_default"])
        medios_pago = list(valores["medios_pago"])
        if not 0 <= recargo_cigarrillos <= 1 or not 0 <= recargo_credito <= 1:
            raise ValueError("Los recargos deben estar entre 0% y 100%.")
        if not 0 <= redondeo <= 4:
            raise ValueError("El redondeo debe estar entre 0 y 4 decimales.")
        if not 0 <= iva_default <= 100:
            raise ValueError("El IVA predeterminado debe estar entre 0% y 100%.")
        if not medios_pago:
            raise ValueError("Debe quedar habilitado al menos un medio de pago.")

        nuevos_valores = {
            "RECARGO_CIGARRILLOS": str(recargo_cigarrillos),
            "RECARGO_CREDITO": str(recargo_credito),
            "REDONDEO_DECIMALES": str(redondeo),
            "IVA_DEFAULT": str(iva_default),
            "MEDIOS_PAGO": ",".join(medios_pago),
            "PERMITIR_STOCK_NEGATIVO": "true" if valores["permitir_stock_negativo"] else "false",
        }
        for clave, valor in nuevos_valores.items():
            configuracion = db.get(ConfiguracionSistema, clave)
            if not configuracion:
                configuracion = ConfiguracionSistema(clave=clave, valor=valor)
                db.add(configuracion)
            configuracion.valor = valor
            configuracion.actualizado_por_id = usuario_id

        db.add(crear_registro_auditoria(
            usuario_id=usuario_id,
            accion="CONFIGURACION_CAJA_MODIFICADA",
            entidad="CONFIGURACION_SISTEMA",
            detalle=nuevos_valores,
            nivel="CRITICO",
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
