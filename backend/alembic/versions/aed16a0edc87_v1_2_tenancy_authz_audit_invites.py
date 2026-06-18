"""v1_2 tenancy authz audit invites

Revision ID: aed16a0edc87
Revises: b1f2c3d4e5a6
Create Date: 2026-06-17 20:40:14.297215
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'aed16a0edc87'
down_revision: Union[str, None] = 'b1f2c3d4e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # v1.2 is not a greenfield-only migration. Existing v1 databases already
    # have users/students/payments/etc., so tenant columns must be introduced as:
    # add nullable -> backfill -> enforce NOT NULL. Old refresh tokens cannot be
    # preserved because v1.2 stores only SHA-256 token hashes and token families;
    # revoking existing sessions is safer than trying to migrate raw JWT rows.
    bind = op.get_bind()

    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=True),
    sa.Column('actor_user_id', sa.Integer(), nullable=True),
    sa.Column('actor_role', sa.String(length=20), nullable=True),
    sa.Column('action', sa.String(length=60), nullable=False),
    sa.Column('entity_type', sa.String(length=40), nullable=True),
    sa.Column('entity_id', sa.String(length=40), nullable=True),
    sa.Column('before', sa.Text(), nullable=True),
    sa.Column('after', sa.Text(), nullable=True),
    sa.Column('ip', sa.String(length=64), nullable=True),
    sa.Column('user_agent', sa.String(length=255), nullable=True),
    sa.Column('request_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_user_id'), 'audit_logs', ['actor_user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_type'), 'audit_logs', ['entity_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_organization_id'), 'audit_logs', ['organization_id'], unique=False)
    op.create_table('organizations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('slug', sa.String(length=60), nullable=False),
    sa.Column('plan', sa.String(length=30), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_slug'), 'organizations', ['slug'], unique=True)

    default_org_id = bind.execute(sa.text("""
        INSERT INTO organizations (name, slug, plan, status)
        VALUES ('EduCore Demo', 'educore', 'standard', 'active')
        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
    """)).scalar_one()

    op.create_table('branches',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_branches_organization_id'), 'branches', ['organization_id'], unique=False)

    default_branch_id = bind.execute(sa.text("""
        INSERT INTO branches (organization_id, name, status)
        VALUES (:org_id, 'Main Branch', 'active')
        RETURNING id
    """), {"org_id": default_org_id}).scalar_one()

    op.create_table('invites',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invites_organization_id'), 'invites', ['organization_id'], unique=False)
    op.create_index(op.f('ix_invites_token_hash'), 'invites', ['token_hash'], unique=True)
    op.create_index(op.f('ix_invites_user_id'), 'invites', ['user_id'], unique=False)

    op.add_column('attendance', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE attendance SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('attendance', 'organization_id', nullable=False)
    op.create_index(op.f('ix_attendance_organization_id'), 'attendance', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'attendance', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    op.add_column('courses', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE courses SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('courses', 'organization_id', nullable=False)
    op.create_index(op.f('ix_courses_organization_id'), 'courses', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'courses', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    op.add_column('groups', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE groups SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('groups', 'organization_id', nullable=False)
    op.create_index(op.f('ix_groups_organization_id'), 'groups', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'groups', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    op.add_column('parents', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE parents SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('parents', 'organization_id', nullable=False)
    op.create_index(op.f('ix_parents_organization_id'), 'parents', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'parents', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    op.add_column('payments', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE payments SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('payments', 'organization_id', nullable=False)
    op.create_index(op.f('ix_payments_organization_id'), 'payments', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'payments', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    bind.execute(sa.text("DELETE FROM refresh_tokens"))
    op.add_column('refresh_tokens', sa.Column('token_hash', sa.String(length=128), nullable=True))
    op.add_column('refresh_tokens', sa.Column('family_id', sa.String(length=32), nullable=True))
    op.add_column('refresh_tokens', sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('refresh_tokens', sa.Column('replaced_by_id', sa.Integer(), nullable=True))
    op.drop_index('ix_refresh_tokens_token', table_name='refresh_tokens')
    op.create_index(op.f('ix_refresh_tokens_family_id'), 'refresh_tokens', ['family_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.drop_column('refresh_tokens', 'token')
    op.alter_column('refresh_tokens', 'token_hash', nullable=False)
    op.alter_column('refresh_tokens', 'family_id', nullable=False)

    op.add_column('students', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE students SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('students', 'organization_id', nullable=False)
    op.create_index(op.f('ix_students_organization_id'), 'students', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'students', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')

    op.add_column('teachers', sa.Column('organization_id', sa.Integer(), nullable=True))
    bind.execute(sa.text("UPDATE teachers SET organization_id = :org_id WHERE organization_id IS NULL"),
                 {"org_id": default_org_id})
    op.alter_column('teachers', 'organization_id', nullable=False)
    op.create_index(op.f('ix_teachers_organization_id'), 'teachers', ['organization_id'], unique=False)
    op.create_foreign_key(None, 'teachers', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    op.add_column('users', sa.Column('organization_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('branch_id', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    bind.execute(sa.text("""
        UPDATE users
        SET organization_id = :org_id,
            branch_id = COALESCE(branch_id, :branch_id),
            status = COALESCE(status, 'active'),
            must_change_password = COALESCE(must_change_password, false),
            token_version = COALESCE(token_version, 0)
        WHERE organization_id IS NULL
    """), {"org_id": default_org_id, "branch_id": default_branch_id})
    op.alter_column('users', 'organization_id', nullable=False)
    op.alter_column('users', 'status', server_default=None)
    op.alter_column('users', 'must_change_password', server_default=None)
    op.alter_column('users', 'token_version', server_default=None)
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    op.create_index(op.f('ix_users_branch_id'), 'users', ['branch_id'], unique=False)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)
    op.create_index(op.f('ix_users_status'), 'users', ['status'], unique=False)
    op.create_foreign_key(None, 'users', 'branches', ['branch_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'users', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_status'), table_name='users')
    op.drop_index(op.f('ix_users_organization_id'), table_name='users')
    op.drop_index(op.f('ix_users_branch_id'), table_name='users')
    op.alter_column('users', 'hashed_password',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'token_version')
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'status')
    op.drop_column('users', 'branch_id')
    op.drop_column('users', 'organization_id')
    op.drop_constraint(None, 'teachers', type_='foreignkey')
    op.drop_index(op.f('ix_teachers_organization_id'), table_name='teachers')
    op.drop_column('teachers', 'organization_id')
    op.drop_constraint(None, 'students', type_='foreignkey')
    op.drop_index(op.f('ix_students_organization_id'), table_name='students')
    op.drop_column('students', 'organization_id')
    op.add_column('refresh_tokens', sa.Column('token', sa.VARCHAR(length=512), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_family_id'), table_name='refresh_tokens')
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True)
    op.drop_column('refresh_tokens', 'replaced_by_id')
    op.drop_column('refresh_tokens', 'revoked_at')
    op.drop_column('refresh_tokens', 'family_id')
    op.drop_column('refresh_tokens', 'token_hash')
    op.drop_constraint(None, 'payments', type_='foreignkey')
    op.drop_index(op.f('ix_payments_organization_id'), table_name='payments')
    op.drop_column('payments', 'organization_id')
    op.drop_constraint(None, 'parents', type_='foreignkey')
    op.drop_index(op.f('ix_parents_organization_id'), table_name='parents')
    op.drop_column('parents', 'organization_id')
    op.drop_constraint(None, 'groups', type_='foreignkey')
    op.drop_index(op.f('ix_groups_organization_id'), table_name='groups')
    op.drop_column('groups', 'organization_id')
    op.drop_constraint(None, 'courses', type_='foreignkey')
    op.drop_index(op.f('ix_courses_organization_id'), table_name='courses')
    op.drop_column('courses', 'organization_id')
    op.drop_constraint(None, 'attendance', type_='foreignkey')
    op.drop_index(op.f('ix_attendance_organization_id'), table_name='attendance')
    op.drop_column('attendance', 'organization_id')
    op.drop_index(op.f('ix_invites_user_id'), table_name='invites')
    op.drop_index(op.f('ix_invites_token_hash'), table_name='invites')
    op.drop_index(op.f('ix_invites_organization_id'), table_name='invites')
    op.drop_table('invites')
    op.drop_index(op.f('ix_branches_organization_id'), table_name='branches')
    op.drop_table('branches')
    op.drop_index(op.f('ix_organizations_slug'), table_name='organizations')
    op.drop_table('organizations')
    op.drop_index(op.f('ix_audit_logs_organization_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    # ### end Alembic commands ###
