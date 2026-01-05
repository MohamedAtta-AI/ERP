"""payroll_group_payslip_audit

Revision ID: 006_payroll_group
Revises: 005_financial
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006_payroll_group'
down_revision: Union[str, None] = '005_financial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PayrollGroup table
    op.create_table(
        'payroll_group',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payroll_group_name'), 'payroll_group', ['name'], unique=False)
    op.create_foreign_key('fk_payroll_group_location', 'payroll_group', 'location', ['location_id'], ['id'])
    
    # Create Payslip table
    op.create_table(
        'payslip',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payroll_run_employee_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', sa.String(length=6), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('pdf_url_ar', sa.String(length=500), nullable=True),
        sa.Column('pdf_url_en', sa.String(length=500), nullable=True),
        sa.Column('language', sa.String(length=2), nullable=False, server_default='ar'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payslip_payroll_run_employee_id'), 'payslip', ['payroll_run_employee_id'], unique=False)
    op.create_index(op.f('ix_payslip_person_id'), 'payslip', ['person_id'], unique=False)
    op.create_foreign_key('fk_payslip_payroll_run_employee', 'payslip', 'payroll_run_employee', ['payroll_run_employee_id'], ['id'])
    op.create_foreign_key('fk_payslip_person', 'payslip', 'person', ['person_id'], ['id'])
    
    # Create AuditLog table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('changed_by_person_id', sa.String(length=6), nullable=True),
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_log_table_name'), 'audit_log', ['table_name'], unique=False)
    op.create_index(op.f('ix_audit_log_record_id'), 'audit_log', ['record_id'], unique=False)
    op.create_index(op.f('ix_audit_log_changed_by_person_id'), 'audit_log', ['changed_by_person_id'], unique=False)
    op.create_index(op.f('ix_audit_log_timestamp'), 'audit_log', ['timestamp'], unique=False)
    op.create_foreign_key('fk_audit_log_changed_by', 'audit_log', 'person', ['changed_by_person_id'], ['id'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('payslip')
    op.drop_table('payroll_group')

