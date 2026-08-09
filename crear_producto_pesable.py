from database.conexion import nueva_sesion
from database.modelos import Producto, Categoria
from services.venta_service import generar_codigo_balanza

db = nueva_sesion()

categoria = db.query(Categoria).filter(Categoria.nombre == "CARNICERIA").first()
if not categoria:
    print("Corré primero: python sembrar_categorias.py")
else:
    if not db.query(Producto).filter(Producto.codigo == "0003").first():
        db.add(Producto(
            codigo="0003",
            plu="00001",
            descripcion="Milanesa de nalga",
            categoria_id=categoria.id,
            precio=8000.0,
            stock=50,
            iva=categoria.iva,
            pesable=True,
        ))
        db.commit()
        print("Producto pesable creado (PLU 00001)")
    else:
        print("Ya existe")

codigo_prueba = generar_codigo_balanza(plu="00001", peso_kg=0.45)
print(f"Código de prueba para simular un escaneo de 450g: {codigo_prueba}")

db.close()