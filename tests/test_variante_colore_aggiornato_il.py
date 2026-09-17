"""Peso_Capsula_api#14 — nessuna tabella di riferimento sapeva quando i
suoi numeri erano stati verificati l'ultima volta; nel foglio Excel di
partenza quella data c'era ed è andata persa nel passaggio. Questi test
coprono `VarianteColore.aggiornato_il`: si aggiorna SOLO quando cambia
la densità, mai al solo rinominare o attivare/disattivare — altrimenti
smetterebbe di voler dire "verificato" e diventerebbe "toccato a
caso"."""


def _crea_colore(db, nome: str, *, gruppo: str = "pvc", densita=None):
    from app.models import VarianteColore

    riga = VarianteColore(nome=nome, gruppo=gruppo, densita_g_m2=densita)
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga


def test_riga_esistente_ha_aggiornato_il_nullo(client, token_admin, db):
    riga = _crea_colore(db, "nero opaco (pvc)")
    r = client.get("/varianti-colore", headers=token_admin)
    corpo = next(v for v in r.json() if v["id"] == riga.id)
    assert corpo["aggiornato_il"] is None


def test_cambiare_la_densita_aggiorna_la_data(client, token_admin, db):
    riga = _crea_colore(db, "nero opaco (pvc)", densita=None)
    assert riga.aggiornato_il is None

    r = client.patch(f"/varianti-colore/{riga.id}", json={"densita_g_m2": 2.5}, headers=token_admin)
    assert r.status_code == 200

    db.refresh(riga)
    assert riga.aggiornato_il is not None


def test_rinominare_NON_aggiorna_la_data(client, token_admin, db):
    """Da verificare al contrario: togliere il controllo su quale campo
    è cambiato (farlo scattare per QUALUNQUE PATCH) e questa prova deve
    diventare rossa — la data smetterebbe di voler dire "densità
    verificata" e direbbe solo "qualcuno ha aperto la riga"."""
    riga = _crea_colore(db, "oro per (pvc)", densita=3.0)
    r = client.patch(f"/varianti-colore/{riga.id}", json={"attivo": False}, headers=token_admin)
    assert r.status_code == 200

    db.refresh(riga)
    assert riga.aggiornato_il is None


def test_disattivare_non_aggiorna_la_data_neanche_dopo_che_era_gia_stata_scritta(client, token_admin, db):
    riga = _crea_colore(db, "oro per (pvc)", densita=3.0)
    client.patch(f"/varianti-colore/{riga.id}", json={"densita_g_m2": 3.5}, headers=token_admin)
    db.refresh(riga)
    prima = riga.aggiornato_il
    assert prima is not None

    client.patch(f"/varianti-colore/{riga.id}", json={"attivo": False}, headers=token_admin)
    db.refresh(riga)
    assert riga.aggiornato_il == prima
