"""righe e colonna mancanti rispetto al foglio Excel

Batti9292/Peso_Capsula_api#7, punti 1-3 — Marco, 16 settembre 2026:
"secondo me mancano dati, mancano caselle". Confronto riga per riga col
foglio originale (colonna C di "dati parete" per i materiali parete,
colonna B di "dati dischi" per i materiali disco):

- 3 materiali parete mancanti nel seed (righe 30/34/38 del foglio),
  aggiunti IN FONDO alla tabella (scelta di Marco nell'issue: "in fondo
  è più semplice e non sposta nulla di esistente");
- 7 materiali disco mancanti (il seed ne aveva solo 2 su 9), stessa
  scelta;
- colonna "my Alu" su materiali_parete (foglio "dati parete" colonna H,
  spessore del solo alluminio) — nessun valore vero inserito qui (le
  tabelle nascono vuote nei numeri, vedi models.py), solo la colonna.

Nessun `codice_commerciale` per le 3 righe nuove: il foglio dà solo il
nome (colonna C) per queste, il commerciale si compila dalla schermata
come per le altre righe vuote già in seed.

Revision ID: 41df057729a2
Revises: 5bbd4fe223c3
Create Date: 2026-09-16 15:13:21.488158

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41df057729a2'
down_revision = '5bbd4fe223c3'
branch_labels = None
depends_on = None

MATERIALI_PARETE_MANCANTI = [
    "26AG4090F",
    "PET 70My BiancoLucido",
    "11TL070F",
]

MATERIALI_DISCO_MANCANTI = [
    "22Ax050F",
    "22Ax070F",
    "80My",
    "DISCHI PVC",
    "23TL110F",
    "DISCHI PET",
    "24TL100F",
]


def upgrade() -> None:
    op.add_column("materiali_parete", sa.Column("my_alu", sa.Float(), nullable=True))

    materiali_parete = sa.table(
        "materiali_parete",
        sa.column("nome", sa.String),
        sa.column("codice_commerciale", sa.String),
        sa.column("attivo", sa.Boolean),
    )
    op.bulk_insert(materiali_parete, [{"nome": n, "codice_commerciale": "", "attivo": True} for n in MATERIALI_PARETE_MANCANTI])

    materiali_disco = sa.table("materiali_disco", sa.column("nome", sa.String))
    op.bulk_insert(materiali_disco, [{"nome": n} for n in MATERIALI_DISCO_MANCANTI])


def downgrade() -> None:
    materiali_disco = sa.table("materiali_disco", sa.column("nome", sa.String))
    op.execute(materiali_disco.delete().where(materiali_disco.c.nome.in_(MATERIALI_DISCO_MANCANTI)))

    materiali_parete = sa.table("materiali_parete", sa.column("nome", sa.String))
    op.execute(materiali_parete.delete().where(materiali_parete.c.nome.in_(MATERIALI_PARETE_MANCANTI)))

    op.drop_column("materiali_parete", "my_alu")
