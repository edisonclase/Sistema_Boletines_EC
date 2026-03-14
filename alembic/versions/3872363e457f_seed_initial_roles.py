"""seed initial roles

Revision ID: 3872363e457f
Revises: 152fa098b946
Create Date: 2026-03-14 09:06:17.805378
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3872363e457f'
down_revision: Union[str, None] = '152fa098b946'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
    )

    op.bulk_insert(
        roles_table,
        [
            {
                "name": "admin",
                "description": "Administrador del sistema CLASE EducTech",
            },
            {
                "name": "registro",
                "description": "Usuario del departamento de Registro Académico",
            },
            {
                "name": "consulta",
                "description": "Usuario con permisos de consulta solamente",
            },
        ],
    )


def downgrade() -> None:

    op.execute(
        """
        DELETE FROM roles
        WHERE name IN ('admin', 'registro', 'consulta')
        """
    )