"""add github data to project

Revision ID: 39d44fcf8e74
Revises: 3b3a9aea8986
Create Date: 2014-10-14 12:44:35.073051

"""

# revision identifiers, used by Alembic.
revision = '39d44fcf8e74'
down_revision = '3b3a9aea8986'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('github_owner', sa.String(length=20), nullable=True))
    op.add_column('project', sa.Column('github_repo', sa.String(length=20), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('project', 'github_repo')
    op.drop_column('project', 'github_owner')
    ### end Alembic commands ###