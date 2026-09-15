"""aggiungi attivo (formati mandrino, materiali parete, varianti colore, fasce disponibili)

Revision ID: c52b14a530ef
Revises: 05c7a2df5757
Create Date: 2026-09-15 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c52b14a530ef'
down_revision = '05c7a2df5757'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default="1": le righe già esistenti diventano attive di
    # default, nessuna sparisce dalla tendina del configuratore col
    # solo fatto di aggiornare il database (Marco, 15 settembre 2026:
    # "attivare o disattivare righe, così che non si mostrino sul
    # configuratore" — di default tutto resta visibile com'è oggi).
    op.add_column('formati_mandrino', sa.Column('attivo', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('materiali_parete', sa.Column('attivo', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('varianti_colore', sa.Column('attivo', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('fasce_disponibili', sa.Column('attivo', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('fasce_disponibili', 'attivo')
    op.drop_column('varianti_colore', 'attivo')
    op.drop_column('materiali_parete', 'attivo')
    op.drop_column('formati_mandrino', 'attivo')
