"""Storico dei calcoli Peso Capsula salvati esplicitamente —
Batti9292/Peso_Capsula_api#9. CONDIVISO come lo storico di Lead Time
(non filtrato per chi lo ha salvato, a differenza di Prezzo Gabbiette):
"il peso di una capsula non è un dato personale di chi ha premuto
Calcola" (Marco, proposta accettata nell'issue in sua assenza).

`GET /storico?limite=N` serve SIA la Dashboard (limite=3) SIA la pagina
Storico (senza limite) — un endpoint solo, non due, come deciso
nell'issue."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from battistella_auth import TokenPayload, richiedi_accesso_app

from ..config import NOME_APP
from ..database import get_db
from ..models import CalcoloRegistrato
from ..schemas import CalcoloRegistratoOut, RegistraCalcoloIn
from .configuratore import risolvi_e_calcola

router = APIRouter(tags=["storico"])
_richiede_accesso = richiedi_accesso_app(NOME_APP)


@router.get("/storico", response_model=list[CalcoloRegistratoOut])
def lista(
    limite: int | None = Query(None, description="Es. 3 per la dashboard, assente per lo storico completo"),
    db: Session = Depends(get_db),
    _utente: TokenPayload = Depends(_richiede_accesso),
):
    # NESSUN filtro per utente, apposta: condiviso con chiunque abbia
    # accesso al modulo, non solo con chi lo ha salvato.
    query = db.query(CalcoloRegistrato).order_by(CalcoloRegistrato.creato_il.desc())
    if limite:
        query = query.limit(limite)
    return query.all()


@router.post("/registra-calcolo", response_model=CalcoloRegistratoOut, status_code=status.HTTP_201_CREATED)
def registra_calcolo(
    dati: RegistraCalcoloIn,
    db: Session = Depends(get_db),
    utente: TokenPayload = Depends(_richiede_accesso),
):
    """Ricalcola da capo lato server (risolvi_e_calcola, la STESSA
    funzione di /calcola) e salva una riga di storico — MAI i pesi
    mandati dal browser: un calcolo che fallisce (formato inesistente,
    valore di riferimento non ancora compilato) solleva la stessa
    HTTPException di /calcola e non lascia nessuna riga a metà."""
    risultato = risolvi_e_calcola(db, dati)

    riga = CalcoloRegistrato(
        creato_da_username=utente.username,
        tipo=dati.tipo,
        formato_codice=dati.formato_codice,
        altezza_capsula=dati.altezza_capsula,
        materiale_parete_nome=dati.materiale_parete_nome,
        materiale_disco_nome=dati.materiale_disco_nome,
        colore_nome=dati.colore_nome or "",
        linguetta=dati.linguetta,
        peso_capsula_g=risultato.peso_capsula_g,
        peso_foglia_parete_g=risultato.peso_foglia_parete_g,
        peso_disco_g=risultato.peso_disco_g,
        peso_colore_g=risultato.peso_colore_g,
        peso_linguetta_g=risultato.peso_linguetta_g,
        fascia_materiale_utilizzata_mm=risultato.fascia_materiale_utilizzata_mm,
        sfrido_rifile_percento=risultato.sfrido_rifile_percento,
    )
    db.add(riga)
    db.commit()
    db.refresh(riga)
    return riga
