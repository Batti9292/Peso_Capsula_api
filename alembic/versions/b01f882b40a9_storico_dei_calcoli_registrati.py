"""storico dei calcoli registrati

Batti9292/Peso_Capsula_api#9 — Marco: "metti in piedi la dashboard e lo
storico". Tabella condivisa (nessun filtro per utente): chiunque abbia
accesso al modulo vede i calcoli salvati da chiunque altro.

Revision ID: b01f882b40a9
Revises: 41df057729a2
Create Date: 2026-09-16 20:29:54.229291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b01f882b40a9'
down_revision = '41df057729a2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calcoli_registrati",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creato_da_username", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("creato_il", sa.DateTime(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("formato_codice", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("altezza_capsula", sa.Float(), nullable=False, server_default="0"),
        sa.Column("materiale_parete_nome", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("materiale_disco_nome", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("colore_nome", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("linguetta", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("peso_capsula_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peso_foglia_parete_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peso_disco_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peso_colore_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("peso_linguetta_g", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fascia_materiale_utilizzata_mm", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sfrido_rifile_percento", sa.Float(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("calcoli_registrati")
