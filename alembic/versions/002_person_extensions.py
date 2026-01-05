"""person_extensions

Revision ID: 002_person
Revises: 001_initial
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_person'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add all Person field extensions
    op.add_column('person', sa.Column('hire_date', sa.Date(), nullable=True))
    op.add_column('person', sa.Column('employment_status', sa.String(), nullable=True))
    op.add_column('person', sa.Column('worker_type', sa.String(), nullable=True))
    op.add_column('person', sa.Column('grade', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('contract_type', sa.String(), nullable=True))
    op.add_column('person', sa.Column('contract_start_date', sa.Date(), nullable=True))
    op.add_column('person', sa.Column('contract_end_date', sa.Date(), nullable=True))
    op.add_column('person', sa.Column('pay_cycle', sa.String(), nullable=True))
    op.add_column('person', sa.Column('payroll_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('person', sa.Column('probation_status', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('person', sa.Column('overtime_eligible', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('person', sa.Column('insurance_enrollment_status', sa.String(), nullable=True))
    op.add_column('person', sa.Column('insurance_number', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('tax_id', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('tax_residency_status', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('payment_method', sa.String(), nullable=True))
    op.add_column('person', sa.Column('bank_name', sa.String(length=100), nullable=True))
    op.add_column('person', sa.Column('iban', sa.String(length=34), nullable=True))
    op.add_column('person', sa.Column('account_number', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('account_holder_name', sa.String(length=255), nullable=True))
    op.add_column('person', sa.Column('branch_code', sa.String(length=20), nullable=True))
    op.add_column('person', sa.Column('wallet_provider', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('wallet_number', sa.String(length=50), nullable=True))
    op.add_column('person', sa.Column('payroll_currency', sa.String(length=3), nullable=False, server_default='EGP'))
    op.add_column('person', sa.Column('payment_status', sa.String(), nullable=True))
    op.add_column('person', sa.Column('password_hash', sa.String(length=255), nullable=True))
    
    # Add foreign key constraint for payroll_group_id
    op.create_foreign_key(
        'fk_person_payroll_group',
        'person', 'payroll_group',
        ['payroll_group_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_person_payroll_group', 'person', type_='foreignkey')
    op.drop_column('person', 'password_hash')
    op.drop_column('person', 'payment_status')
    op.drop_column('person', 'payroll_currency')
    op.drop_column('person', 'wallet_number')
    op.drop_column('person', 'wallet_provider')
    op.drop_column('person', 'branch_code')
    op.drop_column('person', 'account_holder_name')
    op.drop_column('person', 'account_number')
    op.drop_column('person', 'iban')
    op.drop_column('person', 'bank_name')
    op.drop_column('person', 'payment_method')
    op.drop_column('person', 'tax_residency_status')
    op.drop_column('person', 'tax_id')
    op.drop_column('person', 'insurance_number')
    op.drop_column('person', 'insurance_enrollment_status')
    op.drop_column('person', 'overtime_eligible')
    op.drop_column('person', 'probation_status')
    op.drop_column('person', 'payroll_group_id')
    op.drop_column('person', 'pay_cycle')
    op.drop_column('person', 'contract_end_date')
    op.drop_column('person', 'contract_start_date')
    op.drop_column('person', 'contract_type')
    op.drop_column('person', 'grade')
    op.drop_column('person', 'worker_type')
    op.drop_column('person', 'employment_status')
    op.drop_column('person', 'hire_date')

