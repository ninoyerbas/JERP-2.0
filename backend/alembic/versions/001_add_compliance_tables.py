"""Add compliance tables

Revision ID: 001_add_compliance
Revises: 
Create Date: 2024-02-03 01:59:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001_add_compliance'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create compliance tables"""
    
    # Create compliance_violations table
    op.create_table(
        'compliance_violations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('violation_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('standard', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('financial_impact', mysql.DECIMAL(precision=15, scale=2), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for compliance_violations
    op.create_index('ix_compliance_violations_id', 'compliance_violations', ['id'])
    op.create_index('ix_compliance_violations_violation_type', 'compliance_violations', ['violation_type'])
    op.create_index('ix_compliance_violations_severity', 'compliance_violations', ['severity'])
    op.create_index('ix_compliance_violations_standard', 'compliance_violations', ['standard'])
    op.create_index('ix_compliance_violations_resource_type', 'compliance_violations', ['resource_type'])
    op.create_index('ix_compliance_violations_resource_id', 'compliance_violations', ['resource_id'])
    op.create_index('ix_compliance_violations_detected_at', 'compliance_violations', ['detected_at'])
    
    # Create compliance_rules table
    op.create_table(
        'compliance_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('rule_code', sa.String(length=100), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('standard', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('effective_date', sa.DateTime(), nullable=False),
        sa.Column('expiration_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rule_code')
    )
    
    # Create indexes for compliance_rules
    op.create_index('ix_compliance_rules_id', 'compliance_rules', ['id'])
    op.create_index('ix_compliance_rules_rule_code', 'compliance_rules', ['rule_code'], unique=True)
    op.create_index('ix_compliance_rules_rule_type', 'compliance_rules', ['rule_type'])
    op.create_index('ix_compliance_rules_standard', 'compliance_rules', ['standard'])
    op.create_index('ix_compliance_rules_is_active', 'compliance_rules', ['is_active'])
    
    # Create compliance_check_logs table
    op.create_table(
        'compliance_check_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('violations_found', sa.Integer(), default=0, nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('checked_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['checked_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for compliance_check_logs
    op.create_index('ix_compliance_check_logs_id', 'compliance_check_logs', ['id'])
    op.create_index('ix_compliance_check_logs_check_type', 'compliance_check_logs', ['check_type'])
    op.create_index('ix_compliance_check_logs_resource_type', 'compliance_check_logs', ['resource_type'])
    op.create_index('ix_compliance_check_logs_resource_id', 'compliance_check_logs', ['resource_id'])
    op.create_index('ix_compliance_check_logs_checked_at', 'compliance_check_logs', ['checked_at'])


def downgrade() -> None:
    """Drop compliance tables"""
    
    # Drop indexes first
    op.drop_index('ix_compliance_check_logs_checked_at', table_name='compliance_check_logs')
    op.drop_index('ix_compliance_check_logs_resource_id', table_name='compliance_check_logs')
    op.drop_index('ix_compliance_check_logs_resource_type', table_name='compliance_check_logs')
    op.drop_index('ix_compliance_check_logs_check_type', table_name='compliance_check_logs')
    op.drop_index('ix_compliance_check_logs_id', table_name='compliance_check_logs')
    
    op.drop_index('ix_compliance_rules_is_active', table_name='compliance_rules')
    op.drop_index('ix_compliance_rules_standard', table_name='compliance_rules')
    op.drop_index('ix_compliance_rules_rule_type', table_name='compliance_rules')
    op.drop_index('ix_compliance_rules_rule_code', table_name='compliance_rules')
    op.drop_index('ix_compliance_rules_id', table_name='compliance_rules')
    
    op.drop_index('ix_compliance_violations_detected_at', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_resource_id', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_resource_type', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_standard', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_severity', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_violation_type', table_name='compliance_violations')
    op.drop_index('ix_compliance_violations_id', table_name='compliance_violations')
    
    # Drop tables
    op.drop_table('compliance_check_logs')
    op.drop_table('compliance_rules')
    op.drop_table('compliance_violations')
