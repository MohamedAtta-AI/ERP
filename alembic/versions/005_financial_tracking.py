"""financial_tracking

Revision ID: 005_financial
Revises: 004_component
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_financial'
down_revision: Union[str, None] = '004_component'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create SalaryAdvance table
    op.create_table(
        'salary_advance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', sa.String(length=6), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('repayment_component_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_by_person_id', sa.String(length=6), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('taken_date', sa.Date(), nullable=False),
        sa.Column('remaining_balance', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salary_advance_person_id'), 'salary_advance', ['person_id'], unique=False)
    op.create_index(op.f('ix_salary_advance_taken_date'), 'salary_advance', ['taken_date'], unique=False)
    op.create_foreign_key('fk_salary_advance_person', 'salary_advance', 'person', ['person_id'], ['id'])
    op.create_foreign_key('fk_salary_advance_component', 'salary_advance', 'salary_component', ['component_id'], ['id'])
    op.create_foreign_key('fk_salary_advance_repayment', 'salary_advance', 'employee_component', ['repayment_component_id'], ['id'])
    op.create_foreign_key('fk_salary_advance_approved_by', 'salary_advance', 'person', ['approved_by_person_id'], ['id'])
    
    # Create Loan table
    op.create_table(
        'loan',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', sa.String(length=6), nullable=False),
        sa.Column('component_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by_person_id', sa.String(length=6), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('remaining_balance', sa.Float(), nullable=False),
        sa.Column('monthly_installment', sa.Float(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_loan_person_id'), 'loan', ['person_id'], unique=False)
    op.create_index(op.f('ix_loan_start_date'), 'loan', ['start_date'], unique=False)
    op.create_foreign_key('fk_loan_person', 'loan', 'person', ['person_id'], ['id'])
    op.create_foreign_key('fk_loan_component', 'loan', 'salary_component', ['component_id'], ['id'])
    op.create_foreign_key('fk_loan_approved_by', 'loan', 'person', ['approved_by_person_id'], ['id'])


def downgrade() -> None:
    op.drop_table('loan')
    op.drop_table('salary_advance')

