"""Tabelle di riferimento del calcolatore (formati mandrino, materiali
parete/disco, varianti colore, fasce disponibili, costanti per tipo) —
Marco, 15 settembre 2026: "tutti vedono solo il configuratore di peso
... le tabelle di dettaglio in chiaro solo per admin, sviluppatore_admin,
root, e Marco Miotti".

Due livelli di accesso:
- `/nomi` su formati/materiali/colori: SOLO i nomi (niente numeri),
  aperti a chiunque abbia accesso all'app — servono a riempire le
  tendine del configuratore.
- Tutto il resto (elenco completo coi numeri, e ogni PATCH): riservato
  a chi supera `_richiede_dettaglio` sotto.

Mai una POST/DELETE su queste tabelle: "nessuna riga aggiungibile o
togliibile" (Marco) — le righe nascono da una migrazione/seed, qui si
può solo aggiornare un valore già esistente."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from battistella_auth import RANGO, TokenPayload, get_utente_corrente, richiedi_accesso_app

from ..config import NOME_APP
from ..database import get_db
from ..models import (
    CostantiDiscoTipo, CostantiTipoCapsula, FasciaDisponibile, FormatoMandrino, MaterialeDisco, MaterialeParete,
    VarianteColore,
)
from ..schemas import (
    CostantiDiscoTipoOut, CostantiDiscoTipoPatchIn, CostantiTipoCapsulaOut, CostantiTipoCapsulaPatchIn,
    FasciaDisponibileOut, FasciaDisponibilePatchIn, FormatoMandrinoOut, FormatoMandrinoPatchIn, MaterialeDiscoOut,
    MaterialeDiscoPatchIn, MaterialeParetePatchIn, MaterialeParteOut, VarianteColoreNomeOut, VarianteColoreOut,
    VarianteColorePatchIn,
)

router = APIRouter(tags=["riferimenti"])
_richiede_accesso = richiedi_accesso_app(NOME_APP)

# L'id (TokenPayload.sub, MAI lo username: vedi battistella_auth/schemas.py
# sul perché "mai usato per decisioni di sicurezza") di "Marco Miotti"
# nell'Auth Service — Marco, 15 settembre 2026: lui vede le tabelle di
# dettaglio anche se il suo rango (Ufficio Tecnico) non basterebbe da
# solo. Se il suo account venisse mai ricreato, questo id andrebbe
# aggiornato (controllare `SELECT id FROM utenti WHERE username='MM01'`
# sull'Auth Service).
ID_MARCO_MIOTTI = "51"


def _richiede_dettaglio(
    _accesso: TokenPayload = Depends(_richiede_accesso),
    utente: TokenPayload = Depends(get_utente_corrente),
) -> TokenPayload:
    if utente.rango >= RANGO["admin"] or utente.sub == ID_MARCO_MIOTTI:
        return utente
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Permessi insufficienti.")


def _crud_sola_modifica(path: str, Model, SchemaOut, SchemaPatchIn):
    """Fabbrica per le 7 tabelle: GET (elenco completo) + PATCH di una
    riga, entrambe riservate a `_richiede_dettaglio`. Stessa idea di
    cilindri_api/app/routers/riferimenti.py::_crud_riferimento, ma
    senza POST/DELETE — qui le righe sono fisse."""

    @router.get(path, response_model=list[SchemaOut])
    def lista(db: Session = Depends(get_db), _u=Depends(_richiede_dettaglio)):
        return db.query(Model).order_by(Model.id).all()

    @router.patch(path + "/{riga_id}", response_model=SchemaOut)
    def aggiorna(riga_id: int, dati: SchemaPatchIn, db: Session = Depends(get_db), _u=Depends(_richiede_dettaglio)):
        riga = db.query(Model).filter(Model.id == riga_id).first()
        if riga is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Riga non trovata.")
        for campo, valore in dati.model_dump(exclude_unset=True).items():
            setattr(riga, campo, valore)
        db.commit()
        db.refresh(riga)
        return riga

    return lista, aggiorna


_crud_sola_modifica("/formati-mandrino", FormatoMandrino, FormatoMandrinoOut, FormatoMandrinoPatchIn)
_crud_sola_modifica("/materiali-parete", MaterialeParete, MaterialeParteOut, MaterialeParetePatchIn)
_crud_sola_modifica("/materiali-disco", MaterialeDisco, MaterialeDiscoOut, MaterialeDiscoPatchIn)
_crud_sola_modifica("/varianti-colore", VarianteColore, VarianteColoreOut, VarianteColorePatchIn)
_crud_sola_modifica("/fasce-disponibili", FasciaDisponibile, FasciaDisponibileOut, FasciaDisponibilePatchIn)
_crud_sola_modifica("/costanti-tipo-capsula", CostantiTipoCapsula, CostantiTipoCapsulaOut, CostantiTipoCapsulaPatchIn)
_crud_sola_modifica("/costanti-disco-tipo", CostantiDiscoTipo, CostantiDiscoTipoOut, CostantiDiscoTipoPatchIn)


# ---- Solo i nomi, per le tendine del configuratore — aperti a chi ha
# accesso all'app, senza bisogno del permesso di dettaglio. ----


@router.get("/formati-mandrino/nomi", response_model=list[str])
def nomi_formati(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(FormatoMandrino.codice).order_by(FormatoMandrino.codice).all()
    return [r[0] for r in righe]


@router.get("/materiali-parete/nomi", response_model=list[str])
def nomi_materiali_parete(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(MaterialeParete.nome).order_by(MaterialeParete.nome).all()
    return [r[0] for r in righe]


@router.get("/materiali-disco/nomi", response_model=list[str])
def nomi_materiali_disco(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(MaterialeDisco.nome).order_by(MaterialeDisco.nome).all()
    return [r[0] for r in righe]


@router.get("/varianti-colore/nomi", response_model=list[VarianteColoreNomeOut])
def nomi_varianti_colore(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    return db.query(VarianteColore).order_by(VarianteColore.gruppo, VarianteColore.nome).all()

