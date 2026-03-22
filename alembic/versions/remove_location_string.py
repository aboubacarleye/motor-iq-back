"""remove location string from claims, keep only gps_latitude and gps_longitude
"""
revision = 'remove_location_string'
down_revision = 'b27c22175807'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.drop_column('claims', 'location')

def downgrade():
    op.add_column('claims', sa.Column('location', sa.String(length=255), nullable=True))
