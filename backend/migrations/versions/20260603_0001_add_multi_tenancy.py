"""add multi tenancy

Revision ID: 20260603_0001
Revises: 
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa


revision = "20260603_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_tenants_code"), "tenants", ["code"], unique=False)

    with op.batch_alter_table("roles") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f("ix_roles_tenant_id"), ["tenant_id"], unique=False)
        batch_op.create_foreign_key("fk_roles_tenant_id_tenants", "tenants", ["tenant_id"], ["id"])
        batch_op.create_unique_constraint("uq_role_tenant_name", ["tenant_id", "name"])
        batch_op.create_unique_constraint("uq_role_tenant_code", ["tenant_id", "code"])

    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("department", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership_user"),
    )
    op.create_index(op.f("ix_tenant_memberships_tenant_id"), "tenant_memberships", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_tenant_memberships_user_id"), "tenant_memberships", ["user_id"], unique=False)

    for table in ["assets", "asset_params", "operation_logs", "flow_records"]:
        with op.batch_alter_table(table) as batch_op:
            batch_op.add_column(sa.Column("tenant_id", sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f(f"ix_{table}_tenant_id"), ["tenant_id"], unique=False)
            batch_op.create_foreign_key(f"fk_{table}_tenant_id_tenants", "tenants", ["tenant_id"], ["id"])

    with op.batch_alter_table("assets") as batch_op:
        batch_op.create_unique_constraint("uq_asset_tenant_code", ["tenant_id", "code"])
    with op.batch_alter_table("asset_params") as batch_op:
        batch_op.create_unique_constraint("uq_asset_param_tenant_type_name", ["tenant_id", "type", "name"])

    tenants = sa.table("tenants", sa.column("id", sa.Integer), sa.column("name", sa.String), sa.column("code", sa.String), sa.column("status", sa.String))
    op.bulk_insert(tenants, [{"id": 1, "name": "默认租户", "code": "default", "status": "active"}])
    for table in ["roles", "assets", "asset_params", "operation_logs", "flow_records"]:
        op.execute(sa.text(f"UPDATE {table} SET tenant_id = 1 WHERE tenant_id IS NULL"))
    op.execute(sa.text("INSERT INTO tenant_memberships (tenant_id, user_id, role_id, department, status, is_default) SELECT 1, id, role_id, department, status, 1 FROM users WHERE role_id IS NOT NULL"))


def downgrade():
    with op.batch_alter_table("asset_params") as batch_op:
        batch_op.drop_constraint("uq_asset_param_tenant_type_name", type_="unique")
    with op.batch_alter_table("assets") as batch_op:
        batch_op.drop_constraint("uq_asset_tenant_code", type_="unique")
    for table in ["flow_records", "operation_logs", "asset_params", "assets"]:
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"fk_{table}_tenant_id_tenants", type_="foreignkey")
            batch_op.drop_index(batch_op.f(f"ix_{table}_tenant_id"))
            batch_op.drop_column("tenant_id")
    op.drop_index(op.f("ix_tenant_memberships_user_id"), table_name="tenant_memberships")
    op.drop_index(op.f("ix_tenant_memberships_tenant_id"), table_name="tenant_memberships")
    op.drop_table("tenant_memberships")
    with op.batch_alter_table("roles") as batch_op:
        batch_op.drop_constraint("uq_role_tenant_code", type_="unique")
        batch_op.drop_constraint("uq_role_tenant_name", type_="unique")
        batch_op.drop_constraint("fk_roles_tenant_id_tenants", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_roles_tenant_id"))
        batch_op.drop_column("tenant_id")
    op.drop_index(op.f("ix_tenants_code"), table_name="tenants")
    op.drop_table("tenants")
