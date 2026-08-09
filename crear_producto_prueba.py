from database.conexion import nueva_sesion
from database.modelos import Producto, Categoria

db = nueva_sesion()

categoria = db.query(Categoria).filter(Categoria.nombre == "ALMACEN").first()
if not categoria:
    print("Corré primero: python sembrar_categorias.py")
else:
    if not db.query(Producto).filter(Producto.codigo == "0001").first():
        db.add(Producto(
            codigo="0001",
            descripcion="Coca Cola 500ml",
            categoria_id=categoria.id,
            precio=1500.0,
            stock=50,
            iva=categoria.iva,
        ))
        db.commit()
        print("Producto de prueba creado (código 0001)")
    else:
        print("Ya existe")

db.close()