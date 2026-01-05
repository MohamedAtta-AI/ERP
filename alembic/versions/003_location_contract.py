"""location_contract

Revision ID: 003_location
Revises: 002_person
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_location'
down_revision: Union[str, None] = '002_person'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add contract fields to Location
    op.add_column('location', sa.Column('contract_document_url', sa.String(length=500), nullable=True))
    op.add_column('location', sa.Column('contract_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('location', 'contract_name')
    op.drop_column('location', 'contract_document_url')

