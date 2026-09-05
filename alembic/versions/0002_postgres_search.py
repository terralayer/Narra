"""PostgreSQL audiobook search indexes.

Revision ID: 0002
Revises: 0001
"""
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute("CREATE INDEX IF NOT EXISTS ix_releases_title_trgm ON releases USING gin (title gin_trgm_ops)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_releases_search_fts ON releases USING gin (to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(subject,'')))")


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != 'postgresql':
        return
    op.execute('DROP INDEX IF EXISTS ix_releases_search_fts')
    op.execute('DROP INDEX IF EXISTS ix_releases_title_trgm')
