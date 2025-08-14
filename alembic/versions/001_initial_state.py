"""Initial migration - Current database state

Revision ID: initial_state
Revises: 
Create Date: 2025-08-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_state'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Mark current state as migrated - no actual changes"""
    pass

def downgrade():
    """Cannot downgrade from initial state"""
    pass
