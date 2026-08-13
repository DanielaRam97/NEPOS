"""Registra la alicuota por venta y el IVA consolidado por turno.

Revision ID: f2d6a8b13c40
Revises: e91b3a7c4d20
"""

from alembic import op
import sqlalchemy as sa


revision = "f2d6a8b13c40"
down_revision = "e91b3a7c4d20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "detalle_venta",
        sa.Column(
            "iva_tasa",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="21.00",
        ),
    )
    op.add_column(
        "turnos",
        sa.Column("iva_10_5", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "turnos",
        sa.Column("iva_21", sa.Numeric(12, 2), nullable=True),
    )

    categorias_reducidas = (
        "'CARNICERIA', 'CARNICERÍA', 'PANADERIA', 'PANADERÍA'"
    )
    op.execute(
        "UPDATE categorias SET iva = '10.5%' "
        f"WHERE UPPER(TRIM(nombre)) IN ({categorias_reducidas})"
    )
    op.execute(
        "UPDATE categorias SET iva = '21%' "
        f"WHERE UPPER(TRIM(nombre)) NOT IN ({categorias_reducidas})"
    )
    op.execute(
        "UPDATE productos p LEFT JOIN categorias c ON c.id = p.categoria_id "
        "SET p.iva = CASE "
        f"WHEN UPPER(TRIM(c.nombre)) IN ({categorias_reducidas}) "
        "THEN '10.5%' ELSE '21%' END"
    )
    op.execute(
        "UPDATE detalle_venta d "
        "LEFT JOIN productos p ON p.id = d.producto_id "
        "LEFT JOIN categorias c ON c.id = p.categoria_id "
        "SET d.iva_tasa = CASE "
        f"WHEN UPPER(TRIM(c.nombre)) IN ({categorias_reducidas}) "
        "THEN 10.50 ELSE 21.00 END"
    )


def downgrade():
    op.drop_column("turnos", "iva_21")
    op.drop_column("turnos", "iva_10_5")
    op.drop_column("detalle_venta", "iva_tasa")
