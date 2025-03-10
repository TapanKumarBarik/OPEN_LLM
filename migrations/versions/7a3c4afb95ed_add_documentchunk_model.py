"""Add DocumentChunk model

Revision ID: 7a3c4afb95ed
Revises: 2457ed08a69f
Create Date: 2025-03-09 17:22:39.097793

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a3c4afb95ed'
down_revision = '2457ed08a69f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('document_chunk',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', sa.ARRAY(sa.Float()), nullable=True),
    sa.Column('chunk_metadata', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('document_chunk')
    # ### end Alembic commands ###
