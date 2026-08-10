from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def convertir_decimal_finito(
    valor,
    *,
    nombre="El valor",
    minimo=None,
    maximo=None,
    decimales=2,
    interpretar_punto_miles=False,
):
    texto = str(valor if valor is not None else "").strip()
    texto = texto.replace("$", "").replace(" ", "")
    if not texto:
        raise ValueError(f"{nombre} es obligatorio.")
    if "," in texto and "." in texto:
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif interpretar_punto_miles and "." in texto:
        partes = texto.split(".")
        if len(partes) > 1 and all(
            len(parte) == 3 and parte.isdigit()
            for parte in partes[1:]
        ):
            texto = "".join(partes)

    try:
        numero = Decimal(texto)
    except InvalidOperation as error:
        raise ValueError(f"{nombre} debe ser numérico.") from error
    if not numero.is_finite():
        raise ValueError(f"{nombre} debe ser un número finito.")
    if minimo is not None and numero < Decimal(str(minimo)):
        raise ValueError(f"{nombre} no puede ser menor que {minimo}.")
    if maximo is not None and numero > Decimal(str(maximo)):
        raise ValueError(f"{nombre} no puede superar {maximo}.")

    cuantizador = Decimal("1").scaleb(-decimales)
    return float(numero.quantize(cuantizador, rounding=ROUND_HALF_UP))
