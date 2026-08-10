"""normaliza los grupos de precios

Revision ID: e53f91a84c27
Revises: d42e81f73b06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e53f91a84c27"
down_revision: Union[str, None] = "d42e81f73b06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grupos_precio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "nombre",
            name="uq_grupos_precio_nombre",
        ),
    )
    op.add_column(
        "productos",
        sa.Column("grupo_precio_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_productos_grupo_precio_id",
        "productos",
        ["grupo_precio_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_productos_grupo_precio_id",
        "productos",
        "grupos_precio",
        ["grupo_precio_id"],
        ["id"],
        ondelete="SET NULL",
    )

    conexion = op.get_bind()
    conexion.execute(
        sa.text(
            """
            INSERT INTO grupos_precio (nombre, activo)
            SELECT DISTINCT TRIM(grupo_precio), 1
            FROM productos
            WHERE grupo_precio IS NOT NULL
              AND TRIM(grupo_precio) <> ''
            """
        )
    )
    conexion.execute(
        sa.text(
            """
            UPDATE productos AS p
            INNER JOIN grupos_precio AS g
                ON g.nombre = TRIM(p.grupo_precio)
            SET p.grupo_precio_id = g.id
            WHERE p.grupo_precio IS NOT NULL
              AND TRIM(p.grupo_precio) <> ''
            """
        )
    )
    op.drop_column("productos", "grupo_precio")


def downgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("grupo_precio", sa.String(100), nullable=True),
    )
    conexion = op.get_bind()
    conexion.execute(
        sa.text(
            """
            UPDATE productos AS p
            LEFT JOIN grupos_precio AS g
                ON g.id = p.grupo_precio_id
            SET p.grupo_precio = g.nombre
            """
        )
    )
    op.drop_constraint(
        "fk_productos_grupo_precio_id",
        "productos",
        type_="foreignkey",
    )
    op.drop_index(
        "ix_productos_grupo_precio_id",
        table_name="productos",
    )
    op.drop_column("productos", "grupo_precio_id")
    op.drop_table("grupos_precio")
