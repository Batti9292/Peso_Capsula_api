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

from datetime import datetime, timezone

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


def _crud_sola_modifica(path: str, Model, SchemaOut, SchemaPatchIn, dopo_patch=None):
    """Fabbrica per le 7 tabelle: GET (elenco completo) + PATCH di una
    riga, entrambe riservate a `_richiede_dettaglio`. Stessa idea di
    cilindri_api/app/routers/riferimenti.py::_crud_riferimento, ma
    senza POST/DELETE — qui le righe sono fisse.

    `dopo_patch(riga, campi_modificati)`, se passata, gira DOPO aver
    scritto i campi inviati e PRIMA del commit — serve a
    VarianteColore.aggiornato_il (Peso_Capsula_api#14): decide da sola
    se quella PATCH specifica conta come "densità verificata", non lo
    fa la factory generica per tutte e sette le tabelle."""

    @router.get(path, response_model=list[SchemaOut])
    def lista(db: Session = Depends(get_db), _u=Depends(_richiede_dettaglio)):
        return db.query(Model).order_by(Model.id).all()

    @router.patch(path + "/{riga_id}", response_model=SchemaOut)
    def aggiorna(riga_id: int, dati: SchemaPatchIn, db: Session = Depends(get_db), _u=Depends(_richiede_dettaglio)):
        riga = db.query(Model).filter(Model.id == riga_id).first()
        if riga is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Riga non trovata.")
        campi_modificati = dati.model_dump(exclude_unset=True)
        for campo, valore in campi_modificati.items():
            setattr(riga, campo, valore)
        if dopo_patch is not None:
            dopo_patch(riga, campi_modificati)
        db.commit()
        db.refresh(riga)
        return riga

    return lista, aggiorna


def _varianti_colore_dopo_patch(riga: VarianteColore, campi_modificati: dict) -> None:
    # Solo la densità: rinominare o attivare/disattivare non e' una
    # verifica del numero, e non deve muovere la data (vedi il
    # commento sul modello e Peso_Capsula_api#14).
    if "densita_g_m2" in campi_modificati:
        riga.aggiornato_il = datetime.now(timezone.utc)


_crud_sola_modifica("/formati-mandrino", FormatoMandrino, FormatoMandrinoOut, FormatoMandrinoPatchIn)
_crud_sola_modifica("/materiali-parete", MaterialeParete, MaterialeParteOut, MaterialeParetePatchIn)
_crud_sola_modifica("/materiali-disco", MaterialeDisco, MaterialeDiscoOut, MaterialeDiscoPatchIn)
_crud_sola_modifica("/varianti-colore", VarianteColore, VarianteColoreOut, VarianteColorePatchIn, dopo_patch=_varianti_colore_dopo_patch)
_crud_sola_modifica("/fasce-disponibili", FasciaDisponibile, FasciaDisponibileOut, FasciaDisponibilePatchIn)
_crud_sola_modifica("/costanti-tipo-capsula", CostantiTipoCapsula, CostantiTipoCapsulaOut, CostantiTipoCapsulaPatchIn)
_crud_sola_modifica("/costanti-disco-tipo", CostantiDiscoTipo, CostantiDiscoTipoOut, CostantiDiscoTipoPatchIn)


# ---- Solo i nomi, per le tendine del configuratore — aperti a chi ha
# accesso all'app, senza bisogno del permesso di dettaglio. ----


# Mappa tipo capsula -> lettera di "gruppo" dei formati mandrino
# compatibili (Marco, 15 settembre 2026: "C" capsuloni, "F" futura, "P"
# pet/pvc). "M" è Magnum — un tipo non ancora supportato dal
# configuratore — e resta SEMPRE disattivato via `attivo` (Marco lo
# disattiva a mano insieme alle righe senza lettera): non è escluso
# qui apposta, per non filtrarlo due volte — se un giorno viene
# riattivato deve comparire comunque in OGNI tipo ("se attivate falle
# vedere sempre"), non restare invisibile perché la sua lettera non
# combacia con nessun tipo. "convex" non ha ancora una lettera
# assegnata (da confermare con Marco): finché manca in questa mappa,
# nomi_formati(tipo="convex") torna tutti i formati attivi, non filtrati.
GRUPPO_PER_TIPO: dict[str, str] = {
    "capsuloni": "C",
    "futura": "F",
    "pvc": "P",
    "pet": "P",
}
# Le uniche lettere che restringono davvero la tendina — un gruppo
# vuoto o una lettera diversa (es. "M") non viene escluso dal filtro,
# vedi il commento sopra.
_GRUPPI_FILTRATI = set(GRUPPO_PER_TIPO.values())

# Peso_Capsula_api#8, parte fattibile SUBITO (il resto aspetta due
# risposte di Marco, vedi l'issue): due mandrini Magnum, marcati per
# errore "P" nel foglio originale (riga scivolata — il terzo mandrino
# della stessa famiglia è marcato "M"), comparivano nelle tendine di
# PVC e PET — lì non li ha mai voluti nessuno. Un elenco di codici
# esatti, non una regola generale: non tocca il resto del filtro,
# ancora "aperto" in attesa di quelle risposte.
_CODICI_MAGNUM_DA_TOGLIERE_DA_PVC_PET = {"M-ø47-7,2°-h185", "M-ø47-7,2°-h230"}


@router.get("/formati-mandrino/nomi", response_model=list[str])
def nomi_formati(tipo: str | None = None, db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(FormatoMandrino).filter(FormatoMandrino.attivo == True).order_by(FormatoMandrino.codice).all()  # noqa: E712
    gruppo_atteso = GRUPPO_PER_TIPO.get(tipo) if tipo else None
    if gruppo_atteso is None:
        return [r.codice for r in righe]
    codici = [r.codice for r in righe if r.gruppo == gruppo_atteso or r.gruppo not in _GRUPPI_FILTRATI]
    if tipo in ("pvc", "pet"):
        codici = [c for c in codici if c not in _CODICI_MAGNUM_DA_TOGLIERE_DA_PVC_PET]
    return codici


@router.get("/materiali-parete/nomi", response_model=list[str])
def nomi_materiali_parete(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(MaterialeParete.nome).filter(MaterialeParete.attivo == True).order_by(MaterialeParete.nome).all()  # noqa: E712
    return [r[0] for r in righe]


@router.get("/materiali-disco/nomi", response_model=list[str])
def nomi_materiali_disco(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    righe = db.query(MaterialeDisco.nome).order_by(MaterialeDisco.nome).all()
    return [r[0] for r in righe]


@router.get("/varianti-colore/nomi", response_model=list[VarianteColoreNomeOut])
def nomi_varianti_colore(db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    return db.query(VarianteColore).filter(VarianteColore.attivo == True).order_by(VarianteColore.gruppo, VarianteColore.nome).all()  # noqa: E712

