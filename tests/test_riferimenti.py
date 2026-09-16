"""GET/PATCH sulle tabelle di riferimento — Marco, 15 settembre 2026:
"tutti vedono solo il configuratore... le tabelle di dettaglio in
chiaro solo per admin, sviluppatore_admin, root, e Marco Miotti"."""

from app.models import FormatoMandrino, MaterialeParete


def _crea_formato(db, **kwargs):
    valori = {"gruppo": "C", "codice": "C-Ø34-1:8"}
    valori.update(kwargs)
    riga = FormatoMandrino(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def _crea_materiale(db, **kwargs):
    valori = {"nome": "COMFORT – 12/40/12"}
    valori.update(kwargs)
    riga = MaterialeParete(**valori)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


# ---------------------------------------------------------------------
# /nomi — aperto a chiunque abbia accesso all'app, niente numeri
# ---------------------------------------------------------------------

def test_nomi_formati_aperto_a_chiunque_abbia_accesso(client, token_utente, db):
    _crea_formato(db, codice="C-Ø34-1:8", diametro_testa=34.0)
    r = client.get("/formati-mandrino/nomi", headers=token_utente)
    assert r.status_code == 200
    assert r.json() == ["C-Ø34-1:8"]
    # Nessun numero nella risposta — solo la stringa del codice.
    assert "34.0" not in r.text


def test_nomi_richiede_comunque_laccesso_allapp(client, token_senza_accesso):
    assert client.get("/formati-mandrino/nomi", headers=token_senza_accesso).status_code == 403


def test_nomi_materiali_parete(client, token_utente, db):
    _crea_materiale(db, nome="COMFORT – 12/40/12")
    r = client.get("/materiali-parete/nomi", headers=token_utente)
    assert r.json() == ["COMFORT – 12/40/12"]


# ---------------------------------------------------------------------
# nomi_formati?tipo= — il gruppo del formato deve combaciare col tipo
# scelto (Marco, 15 settembre 2026: "C" capsuloni, "F" futura, "P"
# pet/pvc, "M" magnum non ancora supportato)
# ---------------------------------------------------------------------

def test_nomi_formati_filtra_per_gruppo_del_tipo(client, token_utente, db):
    _crea_formato(db, gruppo="C", codice="C-1")
    _crea_formato(db, gruppo="F", codice="F-1")
    r = client.get("/formati-mandrino/nomi?tipo=capsuloni", headers=token_utente)
    assert r.json() == ["C-1"]


def test_nomi_formati_senza_tipo_non_filtra(client, token_utente, db):
    _crea_formato(db, gruppo="C", codice="C-1")
    _crea_formato(db, gruppo="F", codice="F-1")
    r = client.get("/formati-mandrino/nomi", headers=token_utente)
    assert sorted(r.json()) == ["C-1", "F-1"]


def test_nomi_formati_tipo_senza_gruppo_assegnato_non_filtra(client, token_utente, db):
    """'convex' non ha ancora una lettera di gruppo confermata da Marco
    — finché manca, non deve nascondere nessun formato attivo."""
    _crea_formato(db, gruppo="C", codice="C-1")
    _crea_formato(db, gruppo="F", codice="F-1")
    r = client.get("/formati-mandrino/nomi?tipo=convex", headers=token_utente)
    assert sorted(r.json()) == ["C-1", "F-1"]


def test_nomi_formati_gruppo_magnum_o_vuoto_sempre_visibile_se_attivo(client, token_utente, db):
    """"M" (Magnum) e i formati senza lettera restano fuori dai tipi
    finché Marco li tiene disattivati — ma se un giorno li riattiva a
    mano devono comparire in OGNI tipo, non restare nascosti perché la
    lettera non combacia (Marco: "se attivate falle vedere sempre")."""
    _crea_formato(db, gruppo="M", codice="M-1")
    _crea_formato(db, gruppo="", codice="SENZA-1")
    r = client.get("/formati-mandrino/nomi?tipo=capsuloni", headers=token_utente)
    assert sorted(r.json()) == ["M-1", "SENZA-1"]


def test_nomi_formati_disattivato_resta_nascosto_anche_col_gruppo_giusto(client, token_admin, token_utente, db):
    riga = _crea_formato(db, gruppo="C", codice="C-1")
    client.patch(f"/formati-mandrino/{riga.id}", json={"attivo": False}, headers=token_admin)
    assert client.get("/formati-mandrino/nomi?tipo=capsuloni", headers=token_utente).json() == []


# ---------------------------------------------------------------------
# Elenco completo e PATCH — riservati a admin+/Marco Miotti
# ---------------------------------------------------------------------

def test_elenco_completo_richiede_il_permesso_di_dettaglio(client, token_utente, token_admin, token_marco_miotti, db):
    _crea_formato(db)
    assert client.get("/formati-mandrino", headers=token_utente).status_code == 403
    assert client.get("/formati-mandrino", headers=token_admin).status_code == 200
    assert client.get("/formati-mandrino", headers=token_marco_miotti).status_code == 200


def test_elenco_completo_mostra_i_numeri(client, token_admin, db):
    _crea_formato(db, diametro_testa=34.0, conicita=8.0)
    r = client.get("/formati-mandrino", headers=token_admin)
    corpo = r.json()[0]
    assert corpo["diametro_testa"] == 34.0
    assert corpo["conicita"] == 8.0


def test_patch_richiede_il_permesso_di_dettaglio(client, token_utente, token_admin, db):
    riga = _crea_formato(db)
    assert client.patch(f"/formati-mandrino/{riga.id}", json={"diametro_testa": 34.0}, headers=token_utente).status_code == 403
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"diametro_testa": 34.0}, headers=token_admin)
    assert r.status_code == 200
    assert r.json()["diametro_testa"] == 34.0


def test_patch_scrive_solo_i_campi_inviati(client, token_admin, db):
    riga = _crea_formato(db, diametro_testa=34.0, conicita=8.0)
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"conicita": 9.0}, headers=token_admin)
    corpo = r.json()
    assert corpo["conicita"] == 9.0
    assert corpo["diametro_testa"] == 34.0  # invariato


def test_patch_non_permette_di_cambiare_il_codice(client, token_admin, db):
    """`codice` non è nello schema di PATCH apposta: è la chiave con cui
    il configuratore sceglie il formato."""
    riga = _crea_formato(db, codice="C-Ø34-1:8")
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"codice": "ALTRO"}, headers=token_admin)
    assert r.status_code == 200
    assert r.json()["codice"] == "C-Ø34-1:8"


def test_patch_su_riga_inesistente_404(client, token_admin):
    assert client.patch("/formati-mandrino/999999", json={"diametro_testa": 1.0}, headers=token_admin).status_code == 404


def test_nessuna_post_o_delete_esposta(client, token_admin):
    """'Nessuna riga aggiungibile o togliibile' (Marco) — non esiste
    nessun endpoint per crearne o eliminarne una."""
    assert client.post("/formati-mandrino", json={"codice": "NUOVO"}, headers=token_admin).status_code in (404, 405)
    assert client.delete("/formati-mandrino/1", headers=token_admin).status_code in (404, 405)


# ---------------------------------------------------------------------
# attivo — nasconde una riga dal configuratore senza cancellarla
# (Marco, 15 settembre 2026)
# ---------------------------------------------------------------------

def test_riga_nuova_e_attiva_di_default(client, token_admin, db):
    riga = _crea_formato(db)
    assert client.get("/formati-mandrino", headers=token_admin).json()[0]["attivo"] is True
    assert riga.attivo is True


def test_riga_disattivata_sparisce_dai_nomi(client, token_admin, token_utente, db):
    riga = _crea_formato(db, codice="C-Ø34-1:8")
    r = client.patch(f"/formati-mandrino/{riga.id}", json={"attivo": False}, headers=token_admin)
    assert r.status_code == 200
    assert r.json()["attivo"] is False
    assert client.get("/formati-mandrino/nomi", headers=token_utente).json() == []


# ---------------------------------------------------------------------
# my_alu — Batti9292/Peso_Capsula_api#7, punto 3 (foglio "dati parete"
# colonna H, spessore del solo alluminio)
# ---------------------------------------------------------------------

def test_my_alu_e_modificabile_via_patch(client, token_admin, db):
    riga = _crea_materiale(db)
    r = client.patch(f"/materiali-parete/{riga.id}", json={"my_alu": 9.0}, headers=token_admin)
    assert r.status_code == 200
    assert r.json()["my_alu"] == 9.0


def test_riga_disattivata_resta_nellelenco_completo(client, token_admin, db):
    """Disattivare non e' cancellare: chi ha il permesso di dettaglio
    continua a vederla e a poterla riattivare."""
    riga = _crea_formato(db, codice="C-Ø34-1:8")
    client.patch(f"/formati-mandrino/{riga.id}", json={"attivo": False}, headers=token_admin)
    corpo = client.get("/formati-mandrino", headers=token_admin).json()
    assert len(corpo) == 1
    assert corpo[0]["codice"] == "C-Ø34-1:8"
    assert corpo[0]["attivo"] is False
