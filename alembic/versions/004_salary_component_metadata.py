"""salary_component_metadata

Revision ID: 004_component
Revises: 003_location
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_component'
down_revision: Union[str, None] = '003_location'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add metadata fields to SalaryComponent
    op.add_column('salary_component', sa.Column('taxable', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('salary_component', sa.Column('insurable', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('salary_component', sa.Column('max_amount', sa.Float(), nullable=True))
    op.add_column('salary_component', sa.Column('max_percentage', sa.Float(), nullable=True))
    op.add_column('salary_component', sa.Column('priority', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('salary_component', sa.Column('cost_allocation_rule', sa.Text(), nullable=True))
    
    # Note: ComponentType enum values (INSURANCE, LOAN_INSTALLMENT, etc.) are handled at application level
    # No database migration needed for enum values in SQLModel


def downgrade() -> None:
    op.drop_column('salary_component', 'cost_allocation_rule')
    op.drop_column('salary_component', 'priority')
    op.drop_column('salary_component', 'max_percentage')
    op.drop_column('salary_component', 'max_amount')
    op.drop_column('salary_component', 'insurable')
    op.drop_column('salary_component', 'taxable')

