import unicodedata


CATEGORIAS_IVA_10_5 = {"CARNICERIA", "PANADERIA"}
IVA_GENERAL = 21.0
IVA_REDUCIDO = 10.5


def normalizar_categoria(nombre):
    texto = unicodedata.normalize("NFKD", str(nombre or ""))
    texto = "".join(
        caracter for caracter in texto if not unicodedata.combining(caracter)
    )
    return " ".join(texto.upper().strip().split())


def tasa_iva_por_categoria(nombre):
    if normalizar_categoria(nombre) in CATEGORIAS_IVA_10_5:
        return IVA_REDUCIDO
    return IVA_GENERAL


def iva_categoria_formateado(nombre):
    return "10.5%" if tasa_iva_por_categoria(nombre) == IVA_REDUCIDO else "21%"


def tasa_iva_producto(producto):
    categoria = getattr(producto, "categoria_rel", None)
    if categoria:
        return tasa_iva_por_categoria(categoria.nombre)

    texto = str(getattr(producto, "iva", "") or "").replace("%", "")
    texto = texto.replace(",", ".").strip()
    try:
        tasa = float(texto)
    except ValueError:
        return IVA_GENERAL
    return IVA_REDUCIDO if abs(tasa - IVA_REDUCIDO) < 0.01 else IVA_GENERAL


def separar_iva_incluido(total, tasa):
    total = float(total or 0)
    tasa = float(tasa or 0)
    if total <= 0 or tasa <= 0:
        return total, 0.0
    neto = total / (1 + tasa / 100)
    return neto, total - neto
