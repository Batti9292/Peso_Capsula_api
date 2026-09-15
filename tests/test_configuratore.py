"""POST /calcola — il configuratore vero e proprio. Solo numeri finti
inventati per il test, mai un valore vero del foglio (vedi
tests/test_calcolo.py per il perché)."""

from app.models import CostantiDiscoTipo, CostantiTipoCapsula, FasciaDisponibile, FormatoMandrino, MaterialeDisco, MaterialeParete, VarianteColore


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


def test_calcola_richiede_accesso_allapp(client, token_senza_accesso, db):
    _prepara_capsuloni_completo(db)
    assert client.post("/calcola", json=_base_in(), headers=token_senza_accesso).status_code == 403


def test_calcola_aperto_a_chiunque_abbia_accesso_niente_permesso_di_dettaglio(client, token_utente, db):
    """A differenza delle tabelle di dettaglio, il configuratore è
    aperto a chiunque abbia accesso all'app — non serve essere admin
    né Marco Miotti."""
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(), headers=token_utente)
    assert r.status_code == 200


def test_calcola_torna_un_peso_positivo(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(), headers=token_utente)
    corpo = r.json()
    assert corpo["peso_capsula_g"] > 0
    assert corpo["peso_foglia_parete_g"] > 0
    assert corpo["peso_disco_g"] > 0


def test_calcola_senza_colore_non_pesa_il_colore(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(colore_nome=None), headers=token_utente)
    assert r.json()["peso_colore_g"] == 0.0


def test_calcola_con_colore_pesa_il_colore(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(colore_nome="oro per (All)"), headers=token_utente)
    assert r.json()["peso_colore_g"] > 0.0


def test_calcola_con_linguetta_pesa_di_piu_di_senza(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    senza = client.post("/calcola", json=_base_in(linguetta=False), headers=token_utente).json()
    con = client.post("/calcola", json=_base_in(linguetta=True), headers=token_utente).json()
    assert abs((con["peso_capsula_g"] - senza["peso_capsula_g"]) - 0.032128) < 1e-9


def test_calcola_formato_inesistente_404(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(formato_codice="NON-ESISTE"), headers=token_utente)
    assert r.status_code == 404


def test_calcola_materiale_parete_inesistente_404(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(materiale_parete_nome="NON-ESISTE"), headers=token_utente)
    assert r.status_code == 404


def test_calcola_colore_inesistente_404(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(colore_nome="NON-ESISTE"), headers=token_utente)
    assert r.status_code == 404


def test_calcola_tipo_sconosciuto_400(client, token_utente, db):
    _prepara_capsuloni_completo(db)
    r = client.post("/calcola", json=_base_in(tipo="non-esiste"), headers=token_utente)
    assert r.status_code == 400


def test_calcola_con_formato_non_ancora_configurato_400_non_500(client, token_utente, db):
    """I formati nascono senza numeri (Marco: "anche il foglio Excel è
    sensibile") — usarli prima che qualcuno li configuri deve dare un
    400 chiaro, mai un errore del server."""
    db.add(FormatoMandrino(codice="C-Ø34-1:8"))  # diametro/conicità mai impostati
    db.add(MaterialeParete(nome="COMFORT", massa_per_superficie=0.6))
    db.add(MaterialeDisco(nome="50My", massa_per_superficie=0.5))
    db.add(CostantiTipoCapsula(tipo="capsuloni", altezza_testa_ht=3.0, sormonto_base_b=1.5, rifila_s=2.0, sormonto_disco_manuale=1.0))
    db.add(CostantiDiscoTipo(tipo="capsuloni", diametro_disco_testa=30.0))
    db.commit()
    r = client.post("/calcola", json=_base_in(), headers=token_utente)
    assert r.status_code == 400
    assert "non è ancora stato configurato" in r.json()["detail"]


def test_calcola_pet_usa_il_diametro_disco_di_pvc(client, token_utente, db):
    """La stranezza del foglio originale (vedi calcolo.py) replicata
    fino in fondo: chiedere il calcolo per "pet" deve usare le costanti
    disco registrate sotto "pvc", non sotto "pet"."""
    db.add(FormatoMandrino(codice="P-Ø34-1:25", diametro_testa=34.0, conicita=25.0))
    db.add(MaterialeParete(nome="PET BIANCO", massa_per_superficie=0.4))
    db.add(MaterialeDisco(nome="50My", massa_per_superficie=0.5))
    db.add(CostantiTipoCapsula(tipo="pet", altezza_testa_ht=3.0, sormonto_base_b=1.5, rifila_s=2.0, sormonto_disco_costante=3.5, ha_linguetta=True, peso_linguetta_g=0.03))
    db.add(CostantiDiscoTipo(tipo="pvc", diametro_disco_testa=28.0))
    db.add(CostantiDiscoTipo(tipo="pet", diametro_disco_testa=999.0))  # mai usato: deve essere ignorato
    db.commit()

    r = client.post("/calcola", json=_base_in(
        tipo="pet", formato_codice="P-Ø34-1:25", materiale_parete_nome="PET BIANCO",
    ), headers=token_utente)
    assert r.status_code == 200
    area_attesa_con_28 = 3.14159265358979 * (28.0 / 2) ** 2
    assert abs(r.json()["area_disco_mm2"] - area_attesa_con_28) < 0.01
