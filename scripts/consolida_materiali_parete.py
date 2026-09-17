"""Consolida `materiali_parete`: molte righe erano lo stesso materiale
duplicato due volte (una col nome commerciale, una col codice tecnico
interno) — Marco, 17 settembre 2026, ha chiesto di unificarle in una
sola riga per materiale, tenendo il nome commerciale come "nome"
(la chiave che usa il Configuratore) e spostando la descrizione del
codice tecnico nel campo "codice_commerciale". Nella sezione PVC ha
anche chiesto di rinominare il gruppo "THERMA" e alcune voci PET di
confluire in "PURALINE".

Nessuna formula si rompe unendo/rinominando: "nome" è solo la chiave di
ricerca scelta al momento del calcolo (vedi Configuratore), non un
riferimento permanente — CalcoloRegistrato salva il nome come TESTO
FISSO nello storico apposta per questo (un materiale rinominato non fa
sparire il perché di un calcolo vecchio, vedi il commento sul modello).

Uso:
    venv/Scripts/python.exe scripts/consolida_materiali_parete.py            (solo report, non scrive nulla)
    venv/Scripts/python.exe scripts/consolida_materiali_parete.py --scrivi   (applica davvero)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import MaterialeParete  # noqa: E402

# Ogni voce: (nome_che_sopravvive, [nomi_da_cancellare], nuovo_nome_o_None, nuovo_codice_commerciale_o_None)
# - nuovo_nome=None -> lascia il nome della riga sopravvissuta invariato
# - nuovo_codice_commerciale=None -> lascia il suo codice_commerciale invariato
FUSIONI = [
    # --- Parte 1: coppia nome-commerciale/codice-tecnico, fino a Stardust ---
    ("POLY-LIGHT – 09/40/09", ["20PB0940F"], None, "All. Polilaminato bilaccato 09/40"),
    ("COMFORT – 12/40/12", ["20PB1235F"], None, "All. Polilaminato bilaccato 12/35"),
    ("COMFORT 2 – 09/50/09", ["20PB0950"], None, "All. Polilaminato bilaccato 09/50"),
    ("INTENSE 1 – 20/40/20", ["20PB2040F"], None, "All. Polilaminato bilaccato 20/40"),
    ("INTENSE 2 – 12/60/12", ["20PB1260F"], None, "All. Polilaminato bilaccato 12/60"),
    ("HEAVY – 20/60/20", ["20PB2060F"], None, "All. Polilaminato bilaccato 20/60"),
    ("FUTURA PLUS – 20/80/20", ["20PB2080F"], None, "All. Polilaminato bilaccato 20/80"),
    ("ECO-TIN – 30/40/30", ["20PB3040F"], None, "All. Polilaminato bilaccato 30/40"),
    ("POLY-TIN 1 – 30/70/30", ["20PB3070F"], None, "All. Polilaminato bilaccato 30/70"),
    ("POLY-TIN 2 – 25/80/25", ["20PB2580F"], None, "All. Polilaminato bilaccato 25/80"),
    ("PURE - Al50", ["19AN0050F"], None, "ALLUMINIO 50MY"),
    ("ECO-COMFORT – Al30/Ca40", ["20PC3040F"], None, "CARTA 30/40 - alternativa a 65my"),
    ("ECO-INTENSE – Al20/Ca25/Al20", ["20PC2025F"], None, "CARTA 20/25/20 - alternativa a 80my"),
    # STARDUST - GLITTER: da sola, nessuna riga gemella, non tocco.

    # --- Parte 2: PET ---
    # "PET IndianoTraspLucido" via del tutto (deve fare riferimento a
    # Puraline), tutto il trasparente (65My, 70My, 11TL070F) confluisce
    # nello stesso Puraline generico, e anche "PET" da solo confluisce
    # qui — Marco, 17 settembre 2026: "pet deve finire dentro puraline
    # pet diventando PURALINE" (il nome finale perde "- PET").
    ("PURALINE - PET", ["PET", "PET IndianoTraspLucido", "PET 65My TraspLucido", "PET 70My TraspLucido", "11TL070F"], "PURALINE", "11PET"),
    # bianco lucido: due nomi diversi per la stessa cosa -> un nome nuovo.
    ("11BL065F", ["PET 70My BiancoLucido"], "PURALINE BIANCO LUCIDO", None),

    # --- Parte 3: PVC -> THERMA ---
    # generico + cinese + colorato + trasparente + "THERMA - PVC" preesistente -> un solo THERMA.
    ("PVC", ["PVC CineseTraspLucido", "THERMA - PVC", "PVC 75My colorato", "PVC 75My trasparente", "10TL075F", "10TS075F"], "THERMA", None),
    ("10AC075F", ["PVC 75My argento chiaro"], "THERMA ARGENTO CHIARO", None),
    ("10AS075F", [], "THERMA ARGENTO SCURO", None),
    ("10BL075F", [], "THERMA BIANCO LUCIDO", None),
    ("10BS075F", [], "THERMA BIANCO SATINATO", None),
    ("10GS075F", [], "THERMA GIALLO PAGLIERINO", None),
    ("10NS075F", [], "THERMA NERO SATINATO", None),
    ("10OS075F", [], "THERMA ORO SATINATO", None),
    ("10RL075F", [], "THERMA ROSSO LUCIDO", None),
]


def prepara_operazioni(db):
    """Ritorna (operazioni, non_trovati) senza scrivere nulla.
    operazioni e' una lista di (riga_sopravvissuta, righe_da_cancellare,
    nuovo_nome_o_None, nuovo_codice_o_None). non_trovati elenca i nomi
    che la fusione cita ma che non esistono (mai una cancellazione alla
    cieca)."""
    operazioni = []
    non_trovati = []
    for nome_sopravvive, nomi_da_cancellare, nuovo_nome, nuovo_codice in FUSIONI:
        riga = db.query(MaterialeParete).filter(MaterialeParete.nome == nome_sopravvive).one_or_none()
        if riga is None:
            non_trovati.append(nome_sopravvive)
            continue
        righe_da_cancellare = []
        for nome_cancella in nomi_da_cancellare:
            r = db.query(MaterialeParete).filter(MaterialeParete.nome == nome_cancella).one_or_none()
            if r is None:
                non_trovati.append(nome_cancella)
                continue
            righe_da_cancellare.append(r)
        operazioni.append((riga, righe_da_cancellare, nuovo_nome, nuovo_codice))
    return operazioni, non_trovati


def main() -> None:
    scrivi = "--scrivi" in sys.argv
    db = SessionLocal()
    try:
        operazioni, non_trovati = prepara_operazioni(db)

        totale_cancellate = sum(len(cancella) for _, cancella, _, _ in operazioni)
        print(f"Fusioni: {len(operazioni)}, righe che verrebbero cancellate: {totale_cancellate}")
        for riga, cancella, nuovo_nome, nuovo_codice in operazioni:
            nome_finale = nuovo_nome if nuovo_nome is not None else riga.nome
            codice_finale = nuovo_codice if nuovo_codice is not None else riga.codice_commerciale
            print(f"  {riga.nome!r} + {[r.nome for r in cancella]!r} -> nome={nome_finale!r}, codice_commerciale={codice_finale!r}")

        if non_trovati:
            print(f"\nATTENZIONE: {len(non_trovati)} nomi citati non esistono in materiali_parete (nessuna operazione su questi):")
            for nome in non_trovati:
                print(f"  {nome!r}")

        if not scrivi:
            print("\n(solo report — rilancia con --scrivi per applicare)")
            return

        for riga, cancella, nuovo_nome, nuovo_codice in operazioni:
            if nuovo_nome is not None:
                riga.nome = nuovo_nome
            if nuovo_codice is not None:
                riga.codice_commerciale = nuovo_codice
            for r in cancella:
                db.delete(r)
        db.commit()
        print(f"\nApplicato: {len(operazioni)} fusioni, {totale_cancellate} righe cancellate.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
