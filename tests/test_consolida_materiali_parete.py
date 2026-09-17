"""scripts/consolida_materiali_parete.py — Marco, 17 settembre 2026: molte
righe di `materiali_parete` erano lo stesso materiale duplicato (nome
commerciale + codice tecnico), da unificare in una sola riga per
materiale. Questi test coprono `prepara_operazioni`, che decide COSA
fare senza scrivere nulla — mai una cancellazione su un nome che non
esiste, mai una riga persa senza che il suo codice_commerciale venga
salvato da qualche parte."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models import MaterialeParete  # noqa: E402
from scripts.consolida_materiali_parete import FUSIONI, prepara_operazioni  # noqa: E402


def test_unisce_nome_commerciale_e_codice_tecnico(db):
    db.add(MaterialeParete(nome="POLY-LIGHT – 09/40/09", codice_commerciale=""))
    db.add(MaterialeParete(nome="20PB0940F", codice_commerciale="All. Polilaminato bilaccato 09/40"))
    db.commit()

    operazioni, non_trovati = prepara_operazioni(db)

    op = next(o for o in operazioni if o[0].nome == "POLY-LIGHT – 09/40/09")
    riga, cancella, nuovo_nome, nuovo_codice = op
    assert [r.nome for r in cancella] == ["20PB0940F"]
    assert nuovo_nome is None  # il nome commerciale resta cosi' com'e'
    assert nuovo_codice == "All. Polilaminato bilaccato 09/40"


def test_un_nome_citato_ma_assente_viene_segnalato_non_cancellato(db):
    """Da verificare al contrario: se la funzione cancellasse alla cieca
    (senza controllare che il nome esista), questa prova non troverebbe
    nulla da segnalare."""
    db.add(MaterialeParete(nome="POLY-LIGHT – 09/40/09", codice_commerciale=""))
    # "20PB0940F" NON esiste in questo database di prova.
    db.commit()

    operazioni, non_trovati = prepara_operazioni(db)

    assert "20PB0940F" in non_trovati
    op = next(o for o in operazioni if o[0].nome == "POLY-LIGHT – 09/40/09")
    assert op[1] == []  # nessuna riga da cancellare, non esisteva


def test_pet_confluisce_in_puraline_che_perde_il_suffisso(db):
    db.add(MaterialeParete(nome="PET"))
    db.add(MaterialeParete(nome="PURALINE - PET"))
    db.commit()

    operazioni, _ = prepara_operazioni(db)

    op = next(o for o in operazioni if o[0].nome == "PURALINE - PET")
    riga, cancella, nuovo_nome, nuovo_codice = op
    assert "PET" in [r.nome for r in cancella]
    assert nuovo_nome == "PURALINE"


def test_therma_unisce_sei_righe_in_una(db):
    for nome in ["PVC", "PVC CineseTraspLucido", "THERMA - PVC", "PVC 75My colorato", "PVC 75My trasparente", "10TL075F", "10TS075F"]:
        db.add(MaterialeParete(nome=nome))
    db.commit()

    operazioni, non_trovati = prepara_operazioni(db)

    op = next(o for o in operazioni if o[0].nome == "PVC")
    riga, cancella, nuovo_nome, nuovo_codice = op
    assert nuovo_nome == "THERMA"
    assert len(cancella) == 6
    # nessuno dei sette nomi seminati qui e' fra i "non trovati" — solo
    # le altre fusioni (non seminate in questo db di prova) lo sono.
    nomi_seminati = {"PVC", "PVC CineseTraspLucido", "THERMA - PVC", "PVC 75My colorato", "PVC 75My trasparente", "10TL075F", "10TS075F"}
    assert nomi_seminati.isdisjoint(non_trovati)


def test_argento_scuro_resta_da_solo_senza_cancellare_niente(db):
    db.add(MaterialeParete(nome="10AS075F", codice_commerciale="PVC ARGENTO SCURO"))
    db.commit()

    operazioni, _ = prepara_operazioni(db)

    op = next(o for o in operazioni if o[0].nome == "10AS075F")
    riga, cancella, nuovo_nome, nuovo_codice = op
    assert cancella == []
    assert nuovo_nome == "THERMA ARGENTO SCURO"
    assert nuovo_codice is None  # il codice_commerciale esistente non si tocca


def test_nessun_nome_sopravvissuto_compare_due_volte_nelle_fusioni():
    """Ogni riga superstite deve comparire come bersaglio UNA sola volta —
    se comparisse due volte, una fusione sovrascriverebbe il lavoro
    dell'altra senza che nessuno se ne accorga."""
    sopravvissuti = [nome for nome, *_ in FUSIONI]
    assert len(sopravvissuti) == len(set(sopravvissuti))


def test_nessun_nome_cancellato_e_anche_un_sopravvissuto_altrove():
    """Un nome che viene cancellato da una fusione non puo' essere anche
    il nome-sopravvissuto (o un cancellato) di un'altra fusione — sarebbe
    un riferimento a una riga che a quel punto non esiste piu'."""
    sopravvissuti = {nome for nome, *_ in FUSIONI}
    cancellati = set()
    for _, nomi_da_cancellare, _, _ in FUSIONI:
        for nome in nomi_da_cancellare:
            assert nome not in sopravvissuti, f"{nome!r} e' sia cancellato che sopravvissuto altrove"
            assert nome not in cancellati, f"{nome!r} e' cancellato da due fusioni diverse"
            cancellati.add(nome)


def test_applicare_scrive_davvero_nome_e_codice(db):
    db.add(MaterialeParete(nome="10AC075F", codice_commerciale="PVC ARGENTO CHIARO"))
    db.add(MaterialeParete(nome="PVC 75My argento chiaro", codice_commerciale="10PVC"))
    db.commit()

    operazioni, _ = prepara_operazioni(db)
    for riga, cancella, nuovo_nome, nuovo_codice in operazioni:
        if riga.nome == "10AC075F":
            if nuovo_nome is not None:
                riga.nome = nuovo_nome
            if nuovo_codice is not None:
                riga.codice_commerciale = nuovo_codice
            for r in cancella:
                db.delete(r)
    db.commit()

    superstiti = db.query(MaterialeParete).all()
    assert len(superstiti) == 1
    assert superstiti[0].nome == "THERMA ARGENTO CHIARO"
    assert superstiti[0].codice_commerciale == "PVC ARGENTO CHIARO"
