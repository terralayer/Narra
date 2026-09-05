"""initial Narra schema

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('authors', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False))
    op.create_index('ix_authors_name', 'authors', ['name'], unique=True)
    op.create_table('narrators', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False))
    op.create_index('ix_narrators_name', 'narrators', ['name'], unique=True)
    op.create_table('series', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False))
    op.create_index('ix_series_name', 'series', ['name'], unique=True)
    op.create_table('books', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('title', sa.String(500), nullable=False), sa.Column('author_id', sa.Integer(), sa.ForeignKey('authors.id')), sa.Column('series_id', sa.Integer(), sa.ForeignKey('series.id')), sa.Column('series_number', sa.String(50)))
    op.create_index('ix_books_title', 'books', ['title'])
    op.create_table('editions', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('book_id', sa.Integer(), sa.ForeignKey('books.id'), nullable=False), sa.Column('narrator_id', sa.Integer(), sa.ForeignKey('narrators.id')), sa.Column('publisher', sa.String(255)), sa.Column('language', sa.String(64)), sa.Column('release_year', sa.Integer()), sa.Column('runtime_seconds', sa.Integer()), sa.Column('abridged', sa.Boolean()), sa.Column('isbn', sa.String(32)), sa.Column('asin', sa.String(32)), sa.Column('codec', sa.String(32)), sa.Column('bitrate', sa.String(32)), sa.Column('cover_url', sa.Text()))
    op.create_index('ix_editions_book_id', 'editions', ['book_id'])
    op.create_index('ix_editions_isbn', 'editions', ['isbn'])
    op.create_index('ix_editions_asin', 'editions', ['asin'])
    op.create_table('usenet_groups', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False, unique=True), sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('high_water', sa.Integer(), nullable=False, server_default='0'))
    op.create_table('nntp_providers', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False), sa.Column('host', sa.String(255), nullable=False), sa.Column('port', sa.Integer(), nullable=False, server_default='563'), sa.Column('username', sa.String(255)), sa.Column('password', sa.String(255)), sa.Column('use_ssl', sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column('max_connections', sa.Integer(), nullable=False, server_default='4'), sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table('releases', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('subject', sa.Text(), nullable=False), sa.Column('title', sa.String(500), nullable=False), sa.Column('group_name', sa.String(255), nullable=False), sa.Column('poster', sa.String(255)), sa.Column('posted_at', sa.DateTime()), sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'), sa.Column('completion', sa.Float(), nullable=False, server_default='0'), sa.Column('classification_score', sa.Integer(), nullable=False, server_default='0'), sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column('reasons', sa.Text(), nullable=False, server_default=''), sa.Column('edition_id', sa.Integer(), sa.ForeignKey('editions.id')), sa.Column('created_at', sa.DateTime(), nullable=False))
    op.create_index('ix_releases_title', 'releases', ['title'])
    op.create_index('ix_releases_group_name', 'releases', ['group_name'])
    op.create_index('ix_releases_accepted', 'releases', ['accepted'])
    op.create_table('release_files', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('release_id', sa.Integer(), sa.ForeignKey('releases.id'), nullable=False), sa.Column('name', sa.String(1000), nullable=False), sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'))
    op.create_index('ix_release_files_release_id', 'release_files', ['release_id'])
    op.create_table('usenet_articles', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('release_id', sa.Integer(), sa.ForeignKey('releases.id')), sa.Column('release_file_id', sa.Integer(), sa.ForeignKey('release_files.id')), sa.Column('group_name', sa.String(255), nullable=False), sa.Column('article_number', sa.Integer(), nullable=False), sa.Column('message_id', sa.String(1000), nullable=False), sa.Column('subject', sa.Text(), nullable=False), sa.Column('bytes', sa.Integer(), nullable=False, server_default='0'), sa.Column('segment', sa.Integer()), sa.Column('segment_total', sa.Integer()), sa.UniqueConstraint('message_id', name='uq_message_id'))
    op.create_index('ix_usenet_articles_release_id', 'usenet_articles', ['release_id'])
    op.create_index('ix_usenet_articles_release_file_id', 'usenet_articles', ['release_file_id'])
    op.create_index('ix_usenet_articles_group_name', 'usenet_articles', ['group_name'])
    op.create_index('ix_usenet_articles_article_number', 'usenet_articles', ['article_number'])
    op.create_table('metadata_matches', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('release_id', sa.Integer(), sa.ForeignKey('releases.id'), nullable=False), sa.Column('source', sa.String(64), nullable=False), sa.Column('external_id', sa.String(255)), sa.Column('confidence', sa.Float(), nullable=False, server_default='0'), sa.Column('raw_json', sa.Text(), nullable=False, server_default='{}'))
    op.create_index('ix_metadata_matches_release_id', 'metadata_matches', ['release_id'])
    op.create_table('api_keys', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), nullable=False), sa.Column('key', sa.String(255), nullable=False, unique=True), sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)
    op.create_table('scan_state', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('group_name', sa.String(255), nullable=False, unique=True), sa.Column('last_article', sa.Integer(), nullable=False, server_default='0'), sa.Column('updated_at', sa.DateTime(), nullable=False))


def downgrade():
    for name in ['scan_state', 'api_keys', 'metadata_matches', 'usenet_articles', 'release_files', 'releases', 'nntp_providers', 'usenet_groups', 'editions', 'books', 'series', 'narrators', 'authors']:
        op.drop_table(name)
