from decimal import Decimal, ROUND_HALF_UP

def formatear_moneda(valor) -> str:
    """Da formato de peso argentino: 1500.5 -> '$1.500,50'
    Autor: Autor A (Refactorizado por Gero-AI para Decimal)
    """
    if valor is None:
        valor = 0
    try:
        # Asegurar que sea Decimal para el redondeo
        d = Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Formatear con separador de miles y decimales
        texto = f"{d:,.2f}"
        # Reemplazar formato americano (1,234.56) por argentino (1.234,56)
        texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"${texto}"
    except Exception:
        return "$0,00"


def formatear_cantidad(valor) -> str:
    """Muestra 1 en vez de 1.0, pero conserva decimales para productos pesables (ej: 1.5 kg).
    Autor: Autor A (Refactorizado por Gero-AI para Decimal)
    """
    if valor is None:
        return "0"
    try:
        # Redondear a 3 decimales (stock/balanza)
        d = Decimal(str(valor)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        
        # Eliminar ceros a la derecha innecesarios
        texto = f"{d:f}" # Evitar notación científica
        if "." in texto:
            texto = texto.rstrip("0").rstrip(".")
        return texto
    except Exception:
        return "0"

def redondear_cantidad(valor) -> Decimal:
    """Redondea cantidades a 3 decimales para stock.
    Autor: Gero-AI
    """
    if valor is None: return Decimal("0.000")
    return Decimal(str(valor)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)