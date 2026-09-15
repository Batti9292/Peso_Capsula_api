"""rimuovi prezzo_e_kg da materiali_parete

Revision ID: 5bbd4fe223c3
Revises: c52b14a530ef
Create Date: 2026-09-15 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5bbd4fe223c3'
down_revision = 'c52b14a530ef'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Marco, 15 settembre 2026: "la colonna prezzo puoi togliere, non
    # serve per il calcolo del peso" — era solo informativo nel foglio
    # Excel originale (vedi il commento tolto da models.py), non entra
    # in nessuna formula. batch mode: DROP COLUMN nativo di SQLite
    # richiede una versione recente, batch funziona su qualunque.
    with op.batch_alter_table('materiali_parete') as batch_op:
        batch_op.drop_column('prezzo_e_kg')


def downgrade() -> None:
    with op.batch_alter_table('materiali_parete') as batch_op:
        batch_op.add_column(sa.Column('prezzo_e_kg', sa.Float(), nullable=True))
