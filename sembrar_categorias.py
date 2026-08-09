from database.conexion import nueva_sesion
from database.modelos import Categoria

CATEGORIAS_INICIALES = [
    ("CIGARRILLOS", "21%"),
    ("PANADERIA", "10,5%"),
    ("CARNICERIA", "10,5%"),
    ("ALMACEN", "21%"),
]

db = nueva_sesion()
creadas = 0
for nombre, iva in CATEGORIAS_INICIALES:
    if not db.query(Categoria).filter(Categoria.nombre == nombre).first():
        db.add(Categoria(nombre=nombre, iva=iva))
        creadas += 1
db.commit()
db.close()
print(f"Categorías creadas: {creadas}")