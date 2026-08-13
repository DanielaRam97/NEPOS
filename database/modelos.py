from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from .conexion import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    usuario = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), default="CAJERO")
    activo = Column(Integer, default=1)
    es_soporte = Column(Boolean, default=False, nullable=False)
    protegido = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=True)
    ultimo_acceso = Column(DateTime, nullable=True)
    creado_por_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    actualizado_por_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    fecha_actualizacion = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )


class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(80), unique=True, nullable=False)
    iva = Column(String(10), default="21%")


class Proveedor(Base):
    __tablename__ = "proveedores"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), unique=True, nullable=False)
    telefono = Column(String(30))
    mail = Column(String(120))
    direccion = Column(String(200))


class GrupoPrecio(Base):
    __tablename__ = "grupos_precio"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())

    productos = relationship("Producto", back_populates="grupo_precio_rel")


class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    plu = Column(String(20), unique=True, nullable=True)
    descripcion = Column(String(200), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    costo = Column(Numeric(12, 2, asdecimal=False), default=0)
    incremento = Column(Numeric(6, 4, asdecimal=False), default=0)
    precio = Column(Numeric(12, 2, asdecimal=False), default=0)
    stock = Column(Numeric(12, 3, asdecimal=False), default=0)
    iva = Column(String(10), default="21%")
    pesable = Column(Boolean, default=False)
    activo = Column(Integer, default=1)
    grupo_precio_id = Column(
        Integer,
        ForeignKey("grupos_precio.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pendiente_revision = Column(Boolean, default=False)
    solicitado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_solicitud = Column(DateTime, nullable=True)

    categoria_rel = relationship("Categoria")
    proveedor_rel = relationship("Proveedor")
    grupo_precio_rel = relationship(
        "GrupoPrecio",
        back_populates="productos",
    )
    solicitado_por = relationship("Usuario", foreign_keys=[solicitado_por_id])


class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True)
    turno = Column(String(20), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_apertura = Column(DateTime, server_default=func.now())
    fecha_cierre = Column(DateTime, nullable=True)
    fondo_inicial = Column(Numeric(12, 2, asdecimal=False), default=20000)
    efectivo_declarado = Column(
        Numeric(12, 2, asdecimal=False),
        nullable=True,
    )
    diferencia_caja = Column(
        Numeric(12, 2, asdecimal=False),
        nullable=True,
    )
    iva_10_5 = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    iva_21 = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    observacion_cierre = Column(String(250), nullable=True)
    cerrado_por_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    estado = Column(String(20), default="ABIERTO")

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    cerrado_por = relationship("Usuario", foreign_keys=[cerrado_por_id])
    ventas = relationship("Venta", back_populates="turno_rel")


class Venta(Base):
    __tablename__ = "ventas"
    id = Column(Integer, primary_key=True)
    numero = Column(Integer)
    fecha = Column(DateTime, server_default=func.now())
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    forma_pago = Column(String(20))
    subtotal = Column(Numeric(12, 2, asdecimal=False), default=0)
    recargo = Column(Numeric(12, 2, asdecimal=False), default=0)
    total = Column(Numeric(12, 2, asdecimal=False), default=0)
    efectivo = Column(Numeric(12, 2, asdecimal=False), default=0)
    qr = Column(Numeric(12, 2, asdecimal=False), default=0)
    debito = Column(Numeric(12, 2, asdecimal=False), default=0)
    credito = Column(Numeric(12, 2, asdecimal=False), default=0)
    cuotas = Column(Integer, nullable=True)
    monto_recibido = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    vuelto = Column(Numeric(12, 2, asdecimal=False), default=0)
    anulada = Column(Boolean, default=False)
    fecha_anulacion = Column(DateTime, nullable=True)
    motivo_anulacion = Column(String(200), nullable=True)
    anulada_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    items = relationship("DetalleVenta", back_populates="venta")
    turno_rel = relationship("Turno", back_populates="ventas")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    anulada_por = relationship("Usuario", foreign_keys=[anulada_por_id])
    descuento_promociones = Column(Numeric(12, 2, asdecimal=False), default=0)
    promociones_aplicadas = relationship(
        "VentaPromocion",
        back_populates="venta",
        cascade="all, delete-orphan",
    )


class DetalleVenta(Base):
    __tablename__ = "detalle_venta"
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"))
    cantidad = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    precio_unitario = Column(Numeric(12, 2, asdecimal=False), nullable=False)
    subtotal = Column(Numeric(12, 2, asdecimal=False), nullable=False)
    iva_tasa = Column(Numeric(5, 2, asdecimal=False), nullable=False, default=21)

    venta = relationship("Venta", back_populates="items")
    producto = relationship("Producto")


class Ingreso(Base):
    __tablename__ = "ingresos"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    cantidad = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    costo = Column(Numeric(12, 2, asdecimal=False), nullable=False)
    incremento = Column(Numeric(6, 4, asdecimal=False), nullable=False)
    precio_venta = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    costo_anterior = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    precio_anterior = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    fecha = Column(DateTime, server_default=func.now())

    producto = relationship("Producto")
    proveedor = relationship("Proveedor")
    usuario = relationship("Usuario")


class AjusteStock(Base):
    __tablename__ = "ajustes_stock"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    stock_anterior = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    stock_nuevo = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    diferencia = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    motivo = Column(String(200), nullable=False)
    fecha = Column(DateTime, server_default=func.now())

    producto = relationship("Producto")
    usuario = relationship("Usuario")


class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"), nullable=True)
    tipo = Column(String(30), nullable=False)
    cantidad = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    stock_anterior = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    stock_nuevo = Column(Numeric(12, 3, asdecimal=False), nullable=False)
    motivo = Column(String(200), nullable=False)
    fecha = Column(DateTime, server_default=func.now())

    producto = relationship("Producto")
    usuario = relationship("Usuario")
    venta = relationship("Venta")


class Auditoria(Base):
    __tablename__ = "auditoria"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=True)
    venta_id = Column(Integer, ForeignKey("ventas.id"), nullable=True)
    accion = Column(String(60), nullable=False)
    entidad = Column(String(60), nullable=False)
    entidad_id = Column(Integer, nullable=True)
    detalle = Column(Text, nullable=True)
    nivel = Column(String(20), default="INFO")
    fecha = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario")
    turno = relationship("Turno")
    venta = relationship("Venta")


class ConfiguracionSistema(Base):
    __tablename__ = "configuracion_sistema"
    clave = Column(String(80), primary_key=True)
    valor = Column(String(255), nullable=False)
    tipo = Column(String(20), default="TEXTO")
    descripcion = Column(String(255), nullable=True)
    actualizado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_actualizacion = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    actualizado_por = relationship("Usuario")

class VentaSuspendida(Base):
    __tablename__ = "ventas_suspendidas"
    id = Column(Integer, primary_key=True)
    turno_id = Column(Integer, ForeignKey("turnos.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    nota = Column(String(100), nullable=True)
    datos_json = Column(Text, nullable=False)
    fecha = Column(DateTime, server_default=func.now())

    usuario = relationship("Usuario")
    turno = relationship("Turno")

class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    descripcion = Column(String(255), nullable=True)
    tipo = Column(String(30), nullable=False, default="COMBO_PRECIO")
    precio_promocional = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    porcentaje = Column(Numeric(6, 2, asdecimal=False), nullable=True)
    porcentaje_maximo = Column(Numeric(6, 2, asdecimal=False), nullable=True)
    descuento_fijo = Column(Numeric(12, 2, asdecimal=False), nullable=True)
    cantidad_lleva = Column(Numeric(12, 3, asdecimal=False), nullable=True)
    cantidad_paga = Column(Numeric(12, 3, asdecimal=False), nullable=True)
    cantidad_minima = Column(Numeric(12, 3, asdecimal=False), nullable=True)
    repetible = Column(Boolean, default=True, nullable=False)
    acumulable = Column(Boolean, default=False, nullable=False)
    prioridad = Column(Integer, default=100, nullable=False)
    fecha_desde = Column(DateTime, nullable=True)
    fecha_hasta = Column(DateTime, nullable=True)
    activa = Column(Boolean, default=True, nullable=False)
    creado_por_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=True,
    )
    fecha_creacion = Column(
        DateTime,
        server_default=func.now(),
    )

    creado_por = relationship("Usuario")

    items = relationship(
        "PromocionItem",
        back_populates="promocion",
        cascade="all, delete-orphan",
    )
    ventas_aplicadas = relationship(
        "VentaPromocion",
        back_populates="promocion",
    )


class PromocionItem(Base):
    __tablename__ = "promocion_items"

    id = Column(Integer, primary_key=True)

    promocion_id = Column(
        Integer,
        ForeignKey("promociones.id", ondelete="CASCADE"),
        nullable=False,
    )

    producto_id = Column(
        Integer,
        ForeignKey("productos.id", ondelete="CASCADE"),
        nullable=True,
    )

    grupo_precio_id = Column(
        Integer,
        ForeignKey("grupos_precio.id", ondelete="CASCADE"),
        nullable=True,
    )

    cantidad = Column(
        Numeric(12, 3, asdecimal=False),
        default=1,
        nullable=False,
    )

    promocion = relationship(
        "Promocion",
        back_populates="items",
    )

    producto = relationship("Producto")
    grupo_precio = relationship("GrupoPrecio")

    __table_args__ = (
        CheckConstraint(
            "(producto_id IS NOT NULL AND grupo_precio_id IS NULL) OR "
            "(producto_id IS NULL AND grupo_precio_id IS NOT NULL)",
            name="ck_promocion_item_un_solo_alcance",
        ),
    )


class VentaPromocion(Base):
    """Foto historica de cada promocion aplicada a una venta."""

    __tablename__ = "venta_promociones"

    id = Column(Integer, primary_key=True)
    venta_id = Column(
        Integer,
        ForeignKey("ventas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    promocion_id = Column(
        Integer,
        ForeignKey("promociones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    nombre = Column(String(120), nullable=False)
    tipo = Column(String(30), nullable=False)
    veces = Column(Integer, nullable=False, default=1)
    ahorro = Column(
        Numeric(12, 2, asdecimal=False),
        nullable=False,
        default=0,
    )

    venta = relationship("Venta", back_populates="promociones_aplicadas")
    promocion = relationship("Promocion", back_populates="ventas_aplicadas")
