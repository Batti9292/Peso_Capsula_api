"""Batti9292/Peso_Capsula_api#7: confronto riga per riga col foglio
Excel originale ha trovato 3 materiali parete e 7 materiali disco
mancanti nel seed. Qui si prova la migrazione VERA (upgrade e
downgrade, su un database temporaneo — non gli oggetti SQLAlchemy in
memoria di conftest.py, che bypassano Alembic con
`Base.metadata.create_all` e non direbbero nulla su una migrazione
sbagliata).

Da verificare al contrario: togliere una riga dalla migrazione
41df057729a2, uno di questi conteggi deve diventare rosso."""

import os
import sqlite3
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

BASE_DIR = Path(__file__).resolve().parent.parent

# Il conteggio atteso dopo TUTTE le migrazioni, incluse le 3+7 righe
# mancanti trovate confrontando il foglio Excel: 49 (seed originale) + 3
# (issue #7, punto 1) = 52 materiali parete; 2 (seed originale) + 7
# (issue #7, punto 2) = 9 materiali disco.
ATTESO_MATERIALI_PARETE = 52
ATTESO_MATERIALI_DISCO = 9


@pytest.fixture
def db_migrata(tmp_path, monkeypatch):
    # alembic/env.py legge SEMPRE `app.config.DATABASE_URL` (mai il
    # sqlalchemy.url passato alla Config qui sotto — vedi env.py riga
    # 14), e quel modulo è già importato (da conftest.py) quando questo
    # fixture gira: una variabile d'ambiente impostata ora non
    # cambierebbe la costante già letta. Serve quindi il monkeypatch
    # sull'attributo del modulo, non solo sull'ambiente — altrimenti la
    # migrazione gira sul database vero invece che su quello temporaneo
    # di questo test.
    db_path = tmp_path / "migrazione.db"
    monkeypatch.setattr("app.config.DATABASE_URL", f"sqlite:///{db_path}")
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    command.upgrade(cfg, "head")
    return cfg, db_path


def _conta(db_path, tabella):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {tabella}").fetchone()[0]
    finally:
        con.close()


def test_dopo_la_migrazione_ci_sono_tutti_i_materiali_del_foglio(db_migrata):
    _cfg, db_path = db_migrata
    assert _conta(db_path, "materiali_parete") == ATTESO_MATERIALI_PARETE
    assert _conta(db_path, "materiali_disco") == ATTESO_MATERIALI_DISCO


def test_le_tre_righe_parete_mancanti_ci_sono_per_nome(db_migrata):
    _cfg, db_path = db_migrata
    con = sqlite3.connect(db_path)
    try:
        nomi = {r[0] for r in con.execute("SELECT nome FROM materiali_parete").fetchall()}
    finally:
        con.close()
    for atteso in ("26AG4090F", "PET 70My BiancoLucido", "11TL070F"):
        assert atteso in nomi


def test_my_alu_esiste_ed_e_vuoto_di_default(db_migrata):
    """Le tabelle nascono vuote nei valori numerici (Marco, 15 settembre
    2026) — la colonna deve esistere, il valore no."""
    _cfg, db_path = db_migrata
    con = sqlite3.connect(db_path)
    try:
        colonne = [r[1] for r in con.execute("PRAGMA table_info(materiali_parete)").fetchall()]
        assert "my_alu" in colonne
        valori = {r[0] for r in con.execute("SELECT my_alu FROM materiali_parete").fetchall()}
    finally:
        con.close()
    assert valori == {None}


def test_downgrade_toglie_esattamente_le_righe_aggiunte(db_migrata):
    # Revisione ESPLICITA, non "-1": questa migrazione non è più
    # necessariamente head (Batti9292/Peso_Capsula_api#9 ne ha aggiunta
    # una sopra) — "-1" da head annullerebbe quella, non questa.
    cfg, db_path = db_migrata
    command.downgrade(cfg, "5bbd4fe223c3")
    assert _conta(db_path, "materiali_parete") == ATTESO_MATERIALI_PARETE - 3
    assert _conta(db_path, "materiali_disco") == ATTESO_MATERIALI_DISCO - 7
    con = sqlite3.connect(db_path)
    try:
        colonne = [r[1] for r in con.execute("PRAGMA table_info(materiali_parete)").fetchall()]
    finally:
        con.close()
    assert "my_alu" not in colonne


def test_upgrade_dopo_downgrade_torna_al_conteggio_giusto(db_migrata):
    cfg, db_path = db_migrata
    command.downgrade(cfg, "5bbd4fe223c3")
    command.upgrade(cfg, "head")
    assert _conta(db_path, "materiali_parete") == ATTESO_MATERIALI_PARETE
    assert _conta(db_path, "materiali_disco") == ATTESO_MATERIALI_DISCO
