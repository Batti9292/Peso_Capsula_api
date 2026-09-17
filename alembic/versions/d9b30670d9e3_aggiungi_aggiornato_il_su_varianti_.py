"""aggiungi aggiornato_il su varianti_colore

Peso_Capsula_api#14 — nessuna tabella di riferimento sapeva quando i
suoi numeri erano stati verificati l'ultima volta, e nel foglio Excel
di partenza quella data c'era (01/09/2022 per i colori PVC, 28/03/2025
per l'alluminio) ed e' andata persa nel passaggio.

⚠️ Le righe esistenti restano NULL — non si inventa una data. Metterci
la data della migrazione direbbe che tutti i colori sono stati
verificati oggi, falso. Se Marco vuole recuperare le due date storiche
dal foglio, le mette a mano dopo: e' una sua decisione.

Revision ID: d9b30670d9e3
Revises: b01f882b40a9
Create Date: 2026-09-17 17:10:22.402705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd9b30670d9e3'
down_revision = 'b01f882b40a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("varianti_colore") as batch:
        batch.add_column(sa.Column("aggiornato_il", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("varianti_colore") as batch:
        batch.drop_column("aggiornato_il")
