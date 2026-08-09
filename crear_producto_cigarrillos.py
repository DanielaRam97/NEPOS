from database.conexion import nueva_sesion
from database.modelos import Producto, Categoria

db = nueva_sesion()

categoria = db.query(Categoria).filter(Categoria.nombre == "CIGARRILLOS").first()
if not categoria:
    print("Corré primero: python sembrar_categorias.py")
else:
    if not db.query(Producto).filter(Producto.codigo == "0002").first():
        db.add(Producto(
            codigo="0002",
            descripcion="Marlboro Box",
            categoria_id=categoria.id,
            precio=3500.0,
            stock=30,
            iva=categoria.iva,
        ))
        db.commit()
        print("Producto de prueba (cigarrillos) creado (código 0002)")
    else:
        print("Ya existe")

db.close()