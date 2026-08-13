"""RF Caja: auditoría, configuración, movimientos y vuelto

Revision ID: a71c9e4f2031
Revises: 642691d130ad
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a71c9e4f2031"
down_revision: Union[str, None] = "642691d130ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ventas",
        sa.Column("monto_recibido", sa.Numeric(12, 2, asdecimal=False), nullable=True),
    )
    op.add_column(
        "ventas",
        sa.Column("vuelto", sa.Numeric(12, 2, asdecimal=False), nullable=True),
    )

    op.create_table(
        "movimientos_stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("venta_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 3, asdecimal=False), nullable=False),
        sa.Column("stock_anterior", sa.Numeric(12, 3, asdecimal=False), nullable=False),
        sa.Column("stock_nuevo", sa.Numeric(12, 3, asdecimal=False), nullable=False),
        sa.Column("motivo", sa.String(200), nullable=False),
        sa.Column("fecha", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["producto_id"], ["productos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"]),
    )

    op.create_table(
        "auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("turno_id", sa.Integer(), nullable=True),
        sa.Column("venta_id", sa.Integer(), nullable=True),
        sa.Column("accion", sa.String(60), nullable=False),
        sa.Column("entidad", sa.String(60), nullable=False),
        sa.Column("entidad_id", sa.Integer(), nullable=True),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.Column("nivel", sa.String(20), server_default="INFO"),
        sa.Column("fecha", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["turno_id"], ["turnos.id"]),
        sa.ForeignKeyConstraint(["venta_id"], ["ventas.id"]),
    )

    configuracion = op.create_table(
        "configuracion_sistema",
        sa.Column("clave", sa.String(80), primary_key=True),
        sa.Column("valor", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(20), server_default="TEXTO"),
        sa.Column("descripcion", sa.String(255), nullable=True),
        sa.Column("actualizado_por_id", sa.Integer(), nullable=True),
        sa.Column("fecha_actualizacion", sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actualizado_por_id"], ["usuarios.id"]),
    )
    op.bulk_insert(configuracion, [
        {"clave": "RECARGO_CIGARRILLOS", "valor": "0.15", "tipo": "DECIMAL", "descripcion": "Recargo aplicado a cigarrillos por QR"},
        {"clave": "RECARGO_CREDITO", "valor": "0.15", "tipo": "DECIMAL", "descripcion": "Recargo de tarjeta de crédito"},
        {"clave": "REDONDEO_DECIMALES", "valor": "2", "tipo": "ENTERO", "descripcion": "Decimales para importes"},
        {"clave": "IVA_DEFAULT", "valor": "21", "tipo": "DECIMAL", "descripcion": "IVA predeterminado"},
        {"clave": "MEDIOS_PAGO", "valor": "EFECTIVO,QR,DEBITO,CREDITO", "tipo": "LISTA", "descripcion": "Medios de pago habilitados y combinables"},
        {"clave": "PERMITIR_STOCK_NEGATIVO", "valor": "true", "tipo": "BOOLEANO", "descripcion": "Permite vender sin stock durante la transición"},
    ])


def downgrade() -> None:
    op.drop_table("configuracion_sistema")
    op.drop_table("auditoria")
    op.drop_table("movimientos_stock")
    op.drop_column("ventas", "vuelto")
    op.drop_column("ventas", "monto_recibido")
