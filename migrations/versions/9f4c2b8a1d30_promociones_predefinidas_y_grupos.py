"""promociones predefinidas, grupos e historial

Revision ID: 9f4c2b8a1d30
Revises: 0d74b0aa7ab5
Create Date: 2026-07-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f4c2b8a1d30"
down_revision: Union[str, None] = "0d74b0aa7ab5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "promociones",
        sa.Column(
            "tipo",
            sa.String(30),
            nullable=False,
            server_default="COMBO_PRECIO",
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "porcentaje",
            sa.Numeric(6, 2, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "porcentaje_maximo",
            sa.Numeric(6, 2, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "descuento_fijo",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "cantidad_lleva",
            sa.Numeric(12, 3, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "cantidad_paga",
            sa.Numeric(12, 3, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "cantidad_minima",
            sa.Numeric(12, 3, asdecimal=False),
            nullable=True,
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "repetible",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "acumulable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "promociones",
        sa.Column(
            "prioridad",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
    )
    op.add_column(
        "promociones",
        sa.Column("fecha_desde", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "promociones",
        sa.Column("fecha_hasta", sa.DateTime(), nullable=True),
    )

    op.alter_column(
        "promociones",
        "precio_promocional",
        existing_type=sa.Numeric(12, 2, asdecimal=False),
        nullable=True,
    )
    op.execute("UPDATE promociones SET activa = 1 WHERE activa IS NULL")
    op.alter_column(
        "promociones",
        "activa",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.true(),
    )

    op.alter_column(
        "promocion_items",
        "producto_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column(
        "promocion_items",
        sa.Column("grupo_precio_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_promocion_items_grupo_precio_id",
        "promocion_items",
        ["grupo_precio_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_promocion_items_grupo_precio_id",
        "promocion_items",
        "grupos_precio",
        ["grupo_precio_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_check_constraint(
        "ck_promocion_item_un_solo_alcance",
        "promocion_items",
        "("
        "producto_id IS NOT NULL AND grupo_precio_id IS NULL"
        ") OR ("
        "producto_id IS NULL AND grupo_precio_id IS NOT NULL"
        ")",
    )

    op.execute(
        "UPDATE ventas SET descuento_promociones = 0 "
        "WHERE descuento_promociones IS NULL"
    )
    op.alter_column(
        "ventas",
        "descuento_promociones",
        existing_type=sa.Numeric(12, 2, asdecimal=False),
        nullable=False,
        server_default="0",
    )

    op.create_table(
        "venta_promociones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("venta_id", sa.Integer(), nullable=False),
        sa.Column("promocion_id", sa.Integer(), nullable=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column(
            "veces",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "ahorro",
            sa.Numeric(12, 2, asdecimal=False),
            nullable=False,
            server_default="0",
        ),
        sa.ForeignKeyConstraint(
            ["venta_id"],
            ["ventas.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["promocion_id"],
            ["promociones.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_venta_promociones_venta_id",
        "venta_promociones",
        ["venta_id"],
        unique=False,
    )
    op.create_index(
        "ix_venta_promociones_promocion_id",
        "venta_promociones",
        ["promocion_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_venta_promociones_promocion_id",
        table_name="venta_promociones",
    )
    op.drop_index(
        "ix_venta_promociones_venta_id",
        table_name="venta_promociones",
    )
    op.drop_table("venta_promociones")

    op.alter_column(
        "ventas",
        "descuento_promociones",
        existing_type=sa.Numeric(12, 2, asdecimal=False),
        nullable=True,
        server_default=None,
    )

    op.drop_constraint(
        "ck_promocion_item_un_solo_alcance",
        "promocion_items",
        type_="check",
    )
    op.drop_constraint(
        "fk_promocion_items_grupo_precio_id",
        "promocion_items",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_promocion_items_grupo_precio_id",
        table_name="promocion_items",
    )
    op.execute(
        "DELETE FROM promocion_items WHERE producto_id IS NULL"
    )
    op.drop_column("promocion_items", "grupo_precio_id")
    op.alter_column(
        "promocion_items",
        "producto_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.execute(
        "UPDATE promociones SET precio_promocional = 0 "
        "WHERE precio_promocional IS NULL"
    )
    op.alter_column(
        "promociones",
        "precio_promocional",
        existing_type=sa.Numeric(12, 2, asdecimal=False),
        nullable=False,
    )
    op.drop_column("promociones", "fecha_hasta")
    op.drop_column("promociones", "fecha_desde")
    op.drop_column("promociones", "prioridad")
    op.drop_column("promociones", "acumulable")
    op.drop_column("promociones", "repetible")
    op.drop_column("promociones", "cantidad_minima")
    op.drop_column("promociones", "cantidad_paga")
    op.drop_column("promociones", "cantidad_lleva")
    op.drop_column("promociones", "descuento_fijo")
    op.drop_column("promociones", "porcentaje_maximo")
    op.drop_column("promociones", "porcentaje")
    op.drop_column("promociones", "tipo")
