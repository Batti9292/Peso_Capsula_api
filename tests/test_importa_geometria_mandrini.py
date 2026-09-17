"""scripts/importa_geometria_mandrini.py — al seed iniziale (05c7a2df5757)
`formati_mandrino` aveva solo gruppo+codice, `diametro_testa`/`conicita`
restavano NULL per sempre. Marco, 17 settembre 2026, ha fornito il foglio
originale con la geometria vera: questi test coprono `prepara_operazioni`,
la funzione che decide COSA aggiornare senza scrivere nulla — mai un
codice del foglio che diventa una riga nuova, mai una scrittura su un
valore già corretto."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import FormatoMandrino  # noqa: E402
from scripts.importa_geometria_mandrini import GEOMETRIA, prepara_operazioni  # noqa: E402


def test_aggiorna_solo_i_codici_gia_in_tabella(db):
    codice_noto, testa, conicita = GEOMETRIA[0]
    db.add(FormatoMandrino(gruppo="F", codice=codice_noto))
    db.add(FormatoMandrino(gruppo="F", codice="ZZZ-non-nel-foglio"))
    db.commit()

    da_aggiornare, non_trovati = prepara_operazioni(db)

    codici_da_aggiornare = {r.codice for r, *_ in da_aggiornare}
    assert codice_noto in codici_da_aggiornare
    assert "ZZZ-non-nel-foglio" not in codici_da_aggiornare
    # tutti gli altri 109 codici del foglio non sono in tabella: segnalati,
    # non inseriti come righe nuove.
    assert len(non_trovati) == len(GEOMETRIA) - 1


def test_non_tocca_una_riga_gia_col_valore_giusto(db):
    """Da verificare al contrario: se il confronto sparisse (o diventasse
    sempre vero), questa riga finirebbe fra quelle da aggiornare anche
    se è già corretta — la prova deve accorgersene."""
    codice, testa, conicita = GEOMETRIA[0]
    db.add(FormatoMandrino(gruppo="F", codice=codice, diametro_testa=testa, conicita=conicita))
    db.commit()

    da_aggiornare, non_trovati = prepara_operazioni(db)

    assert da_aggiornare == []
    assert non_trovati == [c for c, *_ in GEOMETRIA[1:]]


def test_riga_con_solo_un_valore_diverso_viene_comunque_aggiornata(db):
    codice, testa, conicita = GEOMETRIA[0]
    db.add(FormatoMandrino(gruppo="F", codice=codice, diametro_testa=testa, conicita=None))
    db.commit()

    da_aggiornare, _ = prepara_operazioni(db)

    assert len(da_aggiornare) == 1
    riga, testa_nuovo, conicita_nuovo, testa_vecchio, conicita_vecchio = da_aggiornare[0]
    assert riga.codice == codice
    assert conicita_vecchio is None
    assert conicita_nuovo == conicita


def test_nessun_codice_duplicato_nel_foglio():
    codici = [c for c, *_ in GEOMETRIA]
    assert len(codici) == len(set(codici))


def test_scrivere_applica_davvero_i_valori(db):
    codice, testa, conicita = GEOMETRIA[3]
    db.add(FormatoMandrino(gruppo="F", codice=codice))
    db.commit()

    da_aggiornare, _ = prepara_operazioni(db)
    for riga, t, c, _, _ in da_aggiornare:
        riga.diametro_testa = t
        riga.conicita = c
    db.commit()

    ricaricata = db.query(FormatoMandrino).filter(FormatoMandrino.codice == codice).one()
    assert ricaricata.diametro_testa == testa
    assert ricaricata.conicita == conicita
