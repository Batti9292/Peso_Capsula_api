"""Seed: righe fisse dei dati di riferimento (solo nomi/codici,
mai un numero vero — vedi models.py e il commit che introduce
questo modulo per il perché). "Nessuna riga aggiungibile o
togliibile dopo questa" (Marco, 15 settembre 2026): da qui in poi
solo un PATCH sui valori numerici, mai una nuova riga.

Revision ID: 05c7a2df5757
Revises: 4157f2d26b37
Create Date: 2026-09-15T10:12:32.840073
"""
from alembic import op
import sqlalchemy as sa

revision = '05c7a2df5757'
down_revision = '4157f2d26b37'
branch_labels = None
depends_on = None

TIPI_CAPSULA = ('capsuloni', 'convex', 'futura', 'pvc', 'pet')

HA_LINGUETTA = {'capsuloni': True, 'convex': False, 'futura': False, 'pvc': True, 'pet': True}
CONTEGGIO_FASCE = {'capsuloni': 6, 'convex': 6, 'futura': 6, 'pvc': 17, 'pet': 6}

FORMATI = [
    ('F', 'F-Ø27,9-TP-1:38'),
    ('F', 'F-Ø28,6-TS-1:38'),
    ('F', 'F-Ø29 -TS-1:35'),
    ('F', 'F-Ø28,9-TS-1:38'),
    ('F', 'F-Ø29,2 -TP-1:42'),
    ('F', 'F-Ø29,5-TS-1:35'),
    ('F', 'F-Ø29,23-TS-1:35'),
    ('F', 'F-Ø29,25-TS-1:35'),
    ('F', 'F-Ø29,5-TS VB-1:42'),
    ('F', 'F-Ø29,75-TS-1:35'),
    ('F', 'F-Ø29,75-TS GIR-1:32'),
    ('F', 'F-Ø29,9-TS-1:34'),
    ('F', 'F-Ø29,8-TP-1:35'),
    ('F', 'F-Ø30,2-TP-1:35'),
    ('F', 'F-Ø30,3-TS-1:30'),
    ('F', 'F-Ø30,85-TS-1:35'),
    ('F', 'F-Ø31,10-TS-1:41'),
    ('F', 'F-Ø31,4-TS-1:40'),
    ('F', 'F-Ø31,8-TS-1:40'),
    ('F', 'F-Ø32-TS-1:32'),
    ('F', 'F-Ø32,1-TS-1:40'),
    ('F', 'F-Ø32,5-TS-1:35'),
    ('F', 'F-Ø32,06-TP-1:30'),
    ('F', 'F-Ø33-TS-1:40'),
    ('F', 'F-Ø33,2-TS-1:35'),
    ('F', 'F-Ø33,3-TS-1:35'),
    ('F', 'F-Ø35,9-TS-1:20'),
    ('C', 'C-Ø29,6-1:10,8'),
    ('', 'C-Ø30,25-TP-1:6'),
    ('', 'C-Ø30,25-TP-1:7,5'),
    ('C', 'C-Ø30,6-1:10'),
    ('C', 'C-Ø30,6-1:6'),
    ('C', 'C-Ø30,6-1:8'),
    ('C', 'C-Ø31,5-1:9'),
    ('C', 'C-Ø33-1:10'),
    ('C', 'C-Ø33-1:6'),
    ('C', 'C-Ø34-1:10'),
    ('C', 'C-Ø34-1:10 (853)'),
    ('C', 'C-Ø34-1:6,88'),
    ('C', 'C-Ø34-1:6,78 FER'),
    ('C', 'C-Ø34-1:7,2'),
    ('C', 'C-Ø34-1:8'),
    ('C', 'C-Ø34-1:8 ZON'),
    ('C', 'C-Ø34-1:9,5'),
    ('C', 'C-Ø34-1:9,5 COL'),
    ('C', 'C-Ø35,2-1:12,5'),
    ('C', 'C-Ø35-1:12'),
    ('x', 'C-Ø35,5-1:7,15'),
    ('x', 'C-Ø35,6-1:10 COL'),
    ('x', 'X-Ø34-(3°)-1:9,55'),
    ('x', 'X-Ø34-(3,6°)-1:7,95'),
    ('M', 'X-Ø34-(4°)-1:7,15'),
    ('M', 'X-Ø34-(4,36°)-1:6,5'),
    ('M', 'M-ø38-5,25°-h165'),
    ('M', 'M-ø38-5,25°-h90'),
    ('M', 'M-ø38-4,5°-h185'),
    ('M', 'M-ø38-4,5°-h90'),
    ('M', 'M-ø42-6,25°-h200'),
    ('M', 'M-ø42-6,25°-h190'),
    ('M', 'M-ø47-7,2°-h205'),
    ('P', 'M-ø47-7,2°-h185'),
    ('P', 'M-ø47-7,2°-h230'),
    ('P', 'P-Ø27,7-TP-1:25'),
    ('P', 'P-Ø28-TS-1:25'),
    ('P', 'P-Ø29,25-TP-1:25'),
    ('P', 'P-Ø29,8-TS-1:25'),
    ('P', 'P-Ø30-TF-1:32'),
    ('P', 'P-Ø30-TP-1:25'),
    ('P', 'P-Ø30-TS-1:25'),
    ('P', 'P-Ø30,5-TP-1:25'),
    ('P', 'P-Ø30,5-TS-1:25'),
    ('P', 'P-Ø30-TS-1:28'),
    ('P', 'P-Ø30,7-KLU-1:16'),
    ('P', 'P-Ø30,8-TS-1:25'),
    ('P', 'P-Ø31-TP-1:25'),
    ('P', 'P-Ø31-TS-1:25'),
    ('P', 'P-Ø31,2-TP-1:20'),
    ('P', 'P-Ø31,3-TS-1:25'),
    ('P', 'P-Ø31,5-TP-1:25'),
    ('P', 'P-Ø32-TP-1:25'),
    ('P', 'P-Ø32-TS-1:25'),
    ('P', 'P-Ø32,3-KLU-1:22'),
    ('P', 'P-Ø32,5-TP-1:20'),
    ('P', 'P-Ø32,6-TP-1:25'),
    ('P', 'P-Ø32,5-TS-1:25'),
    ('P', 'P-Ø33-COL-1:25'),
    ('P', 'P-Ø33-FIO-1:25'),
    ('P', 'P-Ø33-MAR-1:25'),
    ('P', 'P-Ø33-TP-1:25'),
    ('P', 'P-Ø33-TS-1:25'),
    ('P', 'P-Ø33,2-TV-1:25'),
    ('P', 'P-Ø33,4-MAR-1:25'),
    ('P', 'P-Ø33,4-TS-1:30'),
    ('P', 'P-Ø33,4-TV-1:30'),
    ('P', 'P-Ø33,5-TF-1:25'),
    ('P', 'P-Ø33,5-TP-1:25'),
    ('P', 'P-Ø33,7-TS-1:25'),
    ('P', 'P-Ø34-TP-1:25'),
    ('P', 'P-Ø34-TS-1:25'),
    ('P', 'P-Ø34,3 -TP-1:20'),
    ('P', 'P-Ø35-TP-1:25'),
    ('P', 'P-Ø35-TS-1:25'),
    ('P', 'P-Ø35,5-DEN-1:22'),
    ('P', 'P-Ø36-TF-1:20'),
    ('P', 'P-Ø36-TP-1:25'),
    ('P', 'P-Ø36,5-TP-1:25'),
    ('P', 'P-Ø37-TS-1:25'),
    ('P', 'P-Ø37,2-TS-1:25'),
    ('P', 'P-Ø38,8-TS-1:17'),
    ('P', 'P-Ø40,2-TP-1:25'),
]

MATERIALI_PARETE = [
    ('POLY-LIGHT – 09/40/09', ''),
    ('20PB0940F', 'All. Polilaminato bilaccato 09/40'),
    ('COMFORT – 12/40/12', ''),
    ('20PB1235F', 'All. Polilaminato bilaccato 12/35'),
    ('COMFORT 2 – 09/50/09', ''),
    ('20PB0950', 'All. Polilaminato bilaccato 09/50'),
    ('INTENSE 1 – 20/40/20', ''),
    ('20PB2040F', 'All. Polilaminato bilaccato 20/40'),
    ('INTENSE 2 – 12/60/12', ''),
    ('20PB1260F', 'All. Polilaminato bilaccato 12/60'),
    ('HEAVY – 20/60/20', ''),
    ('20PB2060F', 'All. Polilaminato bilaccato 20/60'),
    ('FUTURA PLUS – 20/80/20', ''),
    ('20PB2080F', 'All. Polilaminato bilaccato 20/80'),
    ('ECO-TIN – 30/40/30', ''),
    ('20PB3040F', 'All. Polilaminato bilaccato 30/40'),
    ('POLY-TIN 1 – 30/70/30', ''),
    ('20PB3070F', 'All. Polilaminato bilaccato 30/70'),
    ('POLY-TIN 2 – 25/80/25', ''),
    ('20PB2580F', 'All. Polilaminato bilaccato 25/80'),
    ('PURE - Al50', ''),
    ('19AN0050F', 'ALLUMINIO 50MY'),
    ('ECO-COMFORT – Al30/Ca40', ''),
    ('20PC3040F', 'CARTA 30/40 - alternativa a 65my'),
    ('ECO-INTENSE – Al20/Ca25/Al20', ''),
    ('20PC2025F', 'CARTA 20/25/20 - alternativa a 80my'),
    ('STARDUST - GLITTER', ''),
    ('PET', ''),
    ('PURALINE - PET', ''),
    ('PET IndianoTraspLucido', ''),
    ('11BL065F', 'PET BIANCO LUCIDO'),
    ('PET 65My TraspLucido', ''),
    ('PET 70My TraspLucido', '11PET'),
    ('PVC', ''),
    ('PVC CineseTraspLucido', ''),
    ('THERMA - PVC', ''),
    ('PVC 75My argento chiaro', '10PVC'),
    ('10AC075F', 'PVC ARGENTO CHIARO'),
    ('PVC 75My colorato', '10PVC'),
    ('10AS075F', 'PVC ARGENTO SCURO'),
    ('10BL075F', 'PVC BIANCO LUCIDO'),
    ('10BS075F', 'PVC BIANCO SATINATO'),
    ('10GS075F', 'PVC GIALLO SATINATO'),
    ('10NS075F', 'PVC NERO SATINATO + LUCIDO'),
    ('10OS075F', 'PVC ORO SATINATO'),
    ('10RL075F', 'PVC ROSSO LUCIDO'),
    ('PVC 75My trasparente', '10PVC'),
    ('10TL075F', 'PVC TRASPARENTE LUCIDO'),
    ('10TS075F', 'PVC TRASPARENTE SATINATO'),
]

MATERIALI_DISCO = ['50My', '70My']

VARIANTI_PVC = ['colori standard (PVC)', 'nero opaco (pvc)', 'oro per (pvc)', 'perlati (pvc)', 'colori a campione (pvc)']
VARIANTI_ALLUMINIO = ['colori standard (All)', 'nero opaco (All)', 'oro per (All)', 'perlati (All)', 'colori a campione (All)', 'GLITTER', 'OPV']



def upgrade() -> None:
    formati_mandrino = sa.table(
        "formati_mandrino",
        sa.column("gruppo", sa.String), sa.column("codice", sa.String),
    )
    op.bulk_insert(formati_mandrino, [{"gruppo": g, "codice": c} for g, c in FORMATI])

    materiali_parete = sa.table(
        "materiali_parete",
        sa.column("nome", sa.String), sa.column("codice_commerciale", sa.String),
    )
    op.bulk_insert(materiali_parete, [{"nome": n, "codice_commerciale": c} for n, c in MATERIALI_PARETE])

    materiali_disco = sa.table("materiali_disco", sa.column("nome", sa.String))
    op.bulk_insert(materiali_disco, [{"nome": n} for n in MATERIALI_DISCO])

    varianti_colore = sa.table(
        "varianti_colore",
        sa.column("nome", sa.String), sa.column("gruppo", sa.String),
    )
    op.bulk_insert(varianti_colore, [
        *({"nome": n, "gruppo": "pvc"} for n in VARIANTI_PVC),
        *({"nome": n, "gruppo": "alluminio"} for n in VARIANTI_ALLUMINIO),
    ])

    costanti_tipo_capsula = sa.table(
        "costanti_tipo_capsula",
        sa.column("tipo", sa.String), sa.column("ha_linguetta", sa.Boolean), sa.column("peso_linguetta_g", sa.Float),
    )
    op.bulk_insert(costanti_tipo_capsula, [
        {"tipo": t, "ha_linguetta": HA_LINGUETTA[t], "peso_linguetta_g": 0.032128} for t in TIPI_CAPSULA
    ])

    costanti_disco_tipo = sa.table("costanti_disco_tipo", sa.column("tipo", sa.String))
    op.bulk_insert(costanti_disco_tipo, [{"tipo": t} for t in TIPI_CAPSULA])

    fasce_disponibili = sa.table(
        "fasce_disponibili",
        sa.column("tipo", sa.String), sa.column("ordine", sa.Integer),
    )
    righe_fasce = []
    for tipo, conteggio in CONTEGGIO_FASCE.items():
        for ordine in range(1, conteggio + 1):
            righe_fasce.append({"tipo": tipo, "ordine": ordine})
    op.bulk_insert(fasce_disponibili, righe_fasce)


def downgrade() -> None:
    op.execute("DELETE FROM fasce_disponibili")
    op.execute("DELETE FROM costanti_disco_tipo")
    op.execute("DELETE FROM costanti_tipo_capsula")
    op.execute("DELETE FROM varianti_colore")
    op.execute("DELETE FROM materiali_disco")
    op.execute("DELETE FROM materiali_parete")
    op.execute("DELETE FROM formati_mandrino")
