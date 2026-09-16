"""Peso_Capsula_api#6 — "un valore impossibile in tabella dà un peso
NEGATIVO, senza nessun errore". Gli schemi di PATCH accettavano
qualunque numero; qui si prova che ora rifiutano zero/negativo sui
campi fisici (misure, masse, densità, pesi) — le percentuali di sfrido
restano `ge=0` (zero è legittimo, negativo no).

Da verificare al contrario: togliere un `Field(gt=0)` dallo schema, la
prova corrispondente deve tornare rossa (422 -> 200)."""

from app.models import (
    CostantiDiscoTipo, CostantiTipoCapsula, FasciaDisponibile, FormatoMandrino, MaterialeDisco, MaterialeParete,
    VarianteColore,
)


def _crea_formato(db, **kwargs):
    valori = {"gruppo": "C", "codice": "C-Ø34-1:8"}
    valori.update(kwargs)
    riga = FormatoMandrino(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_materiale_parete(db, **kwargs):
    valori = {"nome": "COMFORT"}
    valori.update(kwargs)
    riga = MaterialeParete(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_materiale_disco(db, **kwargs):
    valori = {"nome": "50My"}
    valori.update(kwargs)
    riga = MaterialeDisco(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_colore(db, **kwargs):
    valori = {"nome": "oro per (All)", "gruppo": "alluminio"}
    valori.update(kwargs)
    riga = VarianteColore(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_fascia(db, **kwargs):
    valori = {"tipo": "capsuloni", "ordine": 1}
    valori.update(kwargs)
    riga = FasciaDisponibile(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_costanti_tipo(db, **kwargs):
    valori = {"tipo": "capsuloni"}
    valori.update(kwargs)
    riga = CostantiTipoCapsula(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_costanti_disco(db, **kwargs):
    valori = {"tipo": "capsuloni"}
    valori.update(kwargs)
    riga = CostantiDiscoTipo(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


# ---------------------------------------------------------------------
# formati-mandrino
# ---------------------------------------------------------------------

def test_diametro_testa_negativo_rifiutato(client, token_admin, db):
    riga = _crea_formato(db)
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"diametro_testa": -34.0}, headers=token_admin)
    assert r.status_code == 422


def test_conicita_zero_rifiutata(client, token_admin, db):
    """Prima della correzione, conicita=0 non era solo un dato strano:
    rompeva il servizio con una ZeroDivisionError al primo calcolo."""
    riga = _crea_formato(db)
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"conicita": 0.0}, headers=token_admin)
    assert r.status_code == 422


def test_diametro_testa_positivo_accettato(client, token_admin, db):
    riga = _crea_formato(db)
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"diametro_testa": 34.0}, headers=token_admin)
    assert r.status_code == 200


# ---------------------------------------------------------------------
# materiali-parete
# ---------------------------------------------------------------------

def test_massa_per_superficie_parete_negativa_rifiutata(client, token_admin, db):
    riga = _crea_materiale_parete(db)
    r = client.patch(f"/materiali-parete/{riga.id}", json={"massa_per_superficie": -0.6}, headers=token_admin)
    assert r.status_code == 422


def test_spessore_my_zero_rifiutato(client, token_admin, db):
    riga = _crea_materiale_parete(db)
    r = client.patch(f"/materiali-parete/{riga.id}", json={"spessore_my": 0.0}, headers=token_admin)
    assert r.status_code == 422


# ---------------------------------------------------------------------
# materiali-disco
# ---------------------------------------------------------------------

def test_massa_per_superficie_disco_negativa_rifiutata(client, token_admin, db):
    riga = _crea_materiale_disco(db)
    r = client.patch(f"/materiali-disco/{riga.id}", json={"massa_per_superficie": -0.5}, headers=token_admin)
    assert r.status_code == 422


# ---------------------------------------------------------------------
# varianti-colore
# ---------------------------------------------------------------------

def test_densita_colore_negativa_rifiutata(client, token_admin, db):
    riga = _crea_colore(db)
    r = client.patch(f"/varianti-colore/{riga.id}", json={"densita_g_m2": -80.0}, headers=token_admin)
    assert r.status_code == 422


# ---------------------------------------------------------------------
# fasce-disponibili
# ---------------------------------------------------------------------

def test_larghezza_fascia_zero_rifiutata(client, token_admin, db):
    riga = _crea_fascia(db)
    r = client.patch(f"/fasce-disponibili/{riga.id}", json={"larghezza_mm": 0.0}, headers=token_admin)
    assert r.status_code == 422


# ---------------------------------------------------------------------
# costanti-tipo-capsula
# ---------------------------------------------------------------------

def test_altezza_testa_ht_negativa_rifiutata(client, token_admin, db):
    riga = _crea_costanti_tipo(db)
    r = client.patch(f"/costanti-tipo-capsula/{riga.id}", json={"altezza_testa_ht": -3.0}, headers=token_admin)
    assert r.status_code == 422


def test_peso_linguetta_zero_rifiutato(client, token_admin, db):
    riga = _crea_costanti_tipo(db)
    r = client.patch(f"/costanti-tipo-capsula/{riga.id}", json={"peso_linguetta_g": 0.0}, headers=token_admin)
    assert r.status_code == 422


def test_sfrido_su_lunghezza_zero_e_accettato(client, token_admin, db):
    """Uno sfrido è una percentuale: zero è legittimo (nessuno scarto),
    solo il negativo non ha senso."""
    riga = _crea_costanti_tipo(db)
    r = client.patch(f"/costanti-tipo-capsula/{riga.id}", json={"sfrido_su_lunghezza_percento": 0.0}, headers=token_admin)
    assert r.status_code == 200


def test_sfrido_su_lunghezza_negativo_rifiutato(client, token_admin, db):
    riga = _crea_costanti_tipo(db)
    r = client.patch(f"/costanti-tipo-capsula/{riga.id}", json={"sfrido_su_lunghezza_percento": -1.0}, headers=token_admin)
    assert r.status_code == 422


# ---------------------------------------------------------------------
# costanti-disco-tipo
# ---------------------------------------------------------------------

def test_diametro_disco_testa_negativo_rifiutato(client, token_admin, db):
    riga = _crea_costanti_disco(db)
    r = client.patch(f"/costanti-disco-tipo/{riga.id}", json={"diametro_disco_testa": -30.0}, headers=token_admin)
    assert r.status_code == 422


def test_sfrido_rifile_zero_e_accettato(client, token_admin, db):
    riga = _crea_costanti_disco(db)
    r = client.patch(f"/costanti-disco-tipo/{riga.id}", json={"sfrido_rifile_percento": 0.0}, headers=token_admin)
    assert r.status_code == 200


# ---------------------------------------------------------------------
# /calcola — altezza_capsula è un valore libero scelto da chi compila,
# non letto da una tabella, ma la stessa regola vale
# ---------------------------------------------------------------------

def test_calcola_altezza_capsula_zero_rifiutata_422(client, token_utente, db):
    _crea_formato(db, diametro_testa=34.0, conicita=8.0)
    _crea_materiale_parete(db, massa_per_superficie=0.6)
    _crea_materiale_disco(db, massa_per_superficie=0.5)
    _crea_costanti_tipo(db, altezza_testa_ht=3.0, sormonto_base_b=1.5, rifila_s=2.0, sormonto_disco_manuale=1.0)
    _crea_costanti_disco(db, diametro_disco_testa=30.0)
    r = client.post("/calcola", json={
        "tipo": "capsuloni", "formato_codice": "C-Ø34-1:8", "altezza_capsula": 0.0,
        "materiale_parete_nome": "COMFORT", "materiale_disco_nome": "50My",
    }, headers=token_utente)
    assert r.status_code == 422
