"""Storico dei calcoli registrati — Batti9292/Peso_Capsula_api#9.
CONDIVISO (nessun filtro per utente), e il calcolo si rifà SEMPRE da
capo lato server: mai salvare i pesi mandati dal browser."""

from app.models import CalcoloRegistrato, CostantiDiscoTipo, CostantiTipoCapsula, FasciaDisponibile, FormatoMandrino, MaterialeDisco, MaterialeParete, VarianteColore


def _prepara_capsuloni_completo(db):
    db.add(FormatoMandrino(codice="C-Ø34-1:8", diametro_testa=34.0, conicita=8.0))
    db.add(MaterialeParete(nome="COMFORT", massa_per_superficie=0.6))
    db.add(MaterialeDisco(nome="50My", massa_per_superficie=0.5))
    db.add(VarianteColore(nome="oro per (All)", gruppo="alluminio", densita_g_m2=80.0))
    db.add(CostantiTipoCapsula(
        tipo="capsuloni", altezza_testa_ht=3.0, sormonto_base_b=1.5, rifila_s=2.0,
        sormonto_disco_manuale=1.0, sfrido_su_lunghezza_percento=5.0,
        ha_linguetta=True, peso_linguetta_g=0.032128,
    ))
    db.add(CostantiDiscoTipo(tipo="capsuloni", diametro_disco_testa=30.0))
    for ordine, larghezza in enumerate([30.0, 35.0, 40.0, 50.0], start=1):
        db.add(FasciaDisponibile(tipo="capsuloni", ordine=ordine, larghezza_mm=larghezza))
    db.commit()


def _base_in(**extra) -> dict:
    valori = dict(
        tipo="capsuloni", formato_codice="C-Ø34-1:8", altezza_capsula=30.0,
        materiale_parete_nome="COMFORT", materiale_disco_nome="50My",
    )
    valori.update(extra)
    return valori


# ---------------------------------------------------------------------
# POST /registra-calcolo
# ---------------------------------------------------------------------

def test_registra_calcolo_richiede_accesso_allapp(client, token_senza_accesso, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/registra-calcolo", json=_base_in(), headers=token_senza_accesso)
    assert r.status_code == 403


def test_registra_calcolo_aperto_a_chiunque_abbia_accesso(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/registra-calcolo", json=_base_in(), headers=token_utente)
    assert r.status_code == 201


def test_registra_calcolo_salva_le_scelte_e_il_risultato(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/registra-calcolo", json=_base_in(colore_nome="oro per (All)", linguetta=True), headers=token_utente)
    corpo = r.json()
    assert corpo["tipo"] == "capsuloni"
    assert corpo["formato_codice"] == "C-Ø34-1:8"
    assert corpo["materiale_parete_nome"] == "COMFORT"
    assert corpo["materiale_disco_nome"] == "50My"
    assert corpo["colore_nome"] == "oro per (All)"
    assert corpo["linguetta"] is True
    assert corpo["creato_da_username"] == "collaudo_utente"
    assert corpo["peso_capsula_g"] > 0


def test_registra_calcolo_ignora_i_pesi_mandati_dal_browser(client, token_utente, db):
    """La prova centrale dell'issue: anche mandando dei pesi nel corpo
    della richiesta, il server deve ignorarli e salvare quelli
    RICALCOLATI — mai quelli ricevuti."""
    _prepara_capsuloni_completo(db)
    vero = client.post("/calcola", json=_base_in(), headers=token_utente).json()

    corpo_falsato = _base_in()
    corpo_falsato["peso_capsula_g"] = 999999.0  # ignorato dallo schema di ingresso
    r = client.post("/registra-calcolo", json=corpo_falsato, headers=token_utente)

    salvato = r.json()
    assert salvato["peso_capsula_g"] != 999999.0
    assert abs(salvato["peso_capsula_g"] - vero["peso_capsula_g"]) < 1e-6


def test_registra_calcolo_formato_inesistente_non_lascia_righe(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/registra-calcolo", json=_base_in(formato_codice="NON-ESISTE"), headers=token_utente)
    assert r.status_code == 404
    assert db.query(CalcoloRegistrato).count() == 0


def test_registra_calcolo_formato_non_configurato_400_non_lascia_righe(client, token_utente, db):
    db.add(FormatoMandrino(codice="C-Ø34-1:8"))  # diametro/conicità mai impostati
    db.add(MaterialeParete(nome="COMFORT", massa_per_superficie=0.6))
    db.add(MaterialeDisco(nome="50My", massa_per_superficie=0.5))
    db.add(CostantiTipoCapsula(tipo="capsuloni", altezza_testa_ht=3.0, sormonto_base_b=1.5, rifila_s=2.0, sormonto_disco_manuale=1.0))
    db.add(CostantiDiscoTipo(tipo="capsuloni", diametro_disco_testa=30.0))
    db.commit()
    r = client.post("/registra-calcolo", json=_base_in(), headers=token_utente)
    assert r.status_code == 400
    assert db.query(CalcoloRegistrato).count() == 0


# ---------------------------------------------------------------------
# GET /storico — condiviso, non filtrato per utente
# ---------------------------------------------------------------------

def test_storico_richiede_accesso_allapp(client, token_senza_accesso):
    assert client.get("/storico", headers=token_senza_accesso).status_code == 403


def test_storico_mostra_i_calcoli_di_tutti_non_solo_i_propri(client, token_utente, token_admin, db):
    _prepara_capsuloni_completo(db)
    client.post("/registra-calcolo", json=_base_in(), headers=token_utente)
    client.post("/registra-calcolo", json=_base_in(), headers=token_admin)
    r = client.get("/storico", headers=token_utente)
    usernames = {riga["creato_da_username"] for riga in r.json()}
    assert usernames == {"collaudo_utente", "collaudo_admin"}


def test_storico_limite_torna_le_piu_recenti_in_ordine(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    for altezza in (10.0, 20.0, 30.0, 40.0, 50.0):
        client.post("/registra-calcolo", json=_base_in(altezza_capsula=altezza), headers=token_utente)
    r = client.get("/storico?limite=3", headers=token_utente)
    corpo = r.json()
    assert len(corpo) == 3
    assert [riga["altezza_capsula"] for riga in corpo] == [50.0, 40.0, 30.0]


def test_storico_senza_limite_torna_tutti(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    for altezza in (10.0, 20.0, 30.0):
        client.post("/registra-calcolo", json=_base_in(altezza_capsula=altezza), headers=token_utente)
    r = client.get("/storico", headers=token_utente)
    assert len(r.json()) == 3
