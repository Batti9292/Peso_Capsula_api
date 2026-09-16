"""Il configuratore vero e proprio — Marco, 15 settembre 2026: "tutti
vedono solo il configuratore di peso (altezza libera, formato e
materiale a tendina, presenza linguetta sì/no)". Chi lo chiama sceglie
solo nomi (formato/materiale/colore) e un'altezza; tutti i numeri
veri restano lato server (mai esposti a chi non ha il permesso di
dettaglio, vedi riferimenti.py)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from battistella_auth import TokenPayload, richiedi_accesso_app

from .. import calcolo
from ..config import NOME_APP
from ..database import get_db
from ..models import TIPI_CAPSULA, CostantiDiscoTipo, CostantiTipoCapsula, FasciaDisponibile, FormatoMandrino, MaterialeDisco, MaterialeParete, VarianteColore
from ..schemas import CalcoloIn, CalcoloOut

router = APIRouter(tags=["configuratore"])
_richiede_accesso = richiedi_accesso_app(NOME_APP)


def _numero_o_400(valore: float | None, cosa: str) -> float:
    """I valori nascono `None` (mai un numero vero inserito da chi ha
    scritto questo codice — vedi models.py): se qualcuno usa il
    configuratore prima che una persona autorizzata abbia compilato i
    dati di dettaglio, un 400 chiaro batte uno "None" che esplode
    dentro `calcolo.py` con un TypeError illeggibile."""
    if valore is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"{cosa} non è ancora stato configurato (manca un valore nella tabella di dettaglio).")
    return valore


def risolvi_e_calcola(db: Session, dati: CalcoloIn) -> calcolo.RisultatoCalcolo:
    """Risolve formato/materiali/costanti dal database e chiama
    calcolo.calcola() — condivisa fra /calcola (il configuratore) e
    /registra-calcolo (routers/storico.py): lo storico deve rifare
    ESATTAMENTE lo stesso calcolo, mai una copia che rischia di
    scollarsi da questa (Batti9292/Peso_Capsula_api#9: "il calcolo si
    rifà da capo lato server... mai salvare i pesi mandati dal
    browser")."""
    if dati.tipo not in TIPI_CAPSULA:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f'Tipo capsula sconosciuto: "{dati.tipo}".')

    # `attivo == False` conta come "non trovato" qui: una riga disattivata
    # sparisce dalla tendina del configuratore (vedi riferimenti.py), quindi
    # non deve restare comunque utilizzabile chiamando /calcola direttamente
    # col suo nome/codice.
    formato = db.query(FormatoMandrino).filter(FormatoMandrino.codice == dati.formato_codice, FormatoMandrino.attivo == True).first()  # noqa: E712
    if formato is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f'Formato "{dati.formato_codice}" non trovato.')

    materiale_parete = db.query(MaterialeParete).filter(MaterialeParete.nome == dati.materiale_parete_nome, MaterialeParete.attivo == True).first()  # noqa: E712
    if materiale_parete is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f'Materiale parete "{dati.materiale_parete_nome}" non trovato.')

    materiale_disco = db.query(MaterialeDisco).filter(MaterialeDisco.nome == dati.materiale_disco_nome).first()
    if materiale_disco is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f'Materiale disco "{dati.materiale_disco_nome}" non trovato.')

    densita_colore = 0.0
    if dati.colore_nome is not None:
        colore = db.query(VarianteColore).filter(VarianteColore.nome == dati.colore_nome, VarianteColore.attivo == True).first()  # noqa: E712
        if colore is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f'Colore "{dati.colore_nome}" non trovato.')
        densita_colore = colore.densita_g_m2 or 0.0

    costanti = db.query(CostantiTipoCapsula).filter(CostantiTipoCapsula.tipo == dati.tipo).first()
    if costanti is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f'Costanti mancanti per il tipo "{dati.tipo}" (dato di seed, non dovrebbe succedere).')

    tipo_disco_riferimento = calcolo.diametro_disco_di_riferimento(dati.tipo)
    costanti_disco = db.query(CostantiDiscoTipo).filter(CostantiDiscoTipo.tipo == tipo_disco_riferimento).first()
    if costanti_disco is None:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f'Costanti disco mancanti per il tipo "{tipo_disco_riferimento}" (dato di seed, non dovrebbe succedere).')

    fasce = db.query(FasciaDisponibile).filter(FasciaDisponibile.tipo == dati.tipo, FasciaDisponibile.attivo == True).order_by(FasciaDisponibile.ordine).all()  # noqa: E712
    fasce_mm = tuple(f.larghezza_mm for f in fasce if f.larghezza_mm is not None)

    ingresso = calcolo.InputCalcolo(
        tipo=dati.tipo,
        diametro_testa=_numero_o_400(formato.diametro_testa, f'Il diametro testa del formato "{formato.codice}"'),
        conicita_1a=_numero_o_400(formato.conicita, f'La conicità del formato "{formato.codice}"'),
        altezza_capsula=dati.altezza_capsula,
        altezza_testa_ht=_numero_o_400(costanti.altezza_testa_ht, f'"Altezza testa" per il tipo "{dati.tipo}"'),
        sormonto_base_b=_numero_o_400(costanti.sormonto_base_b, f'"Sormonto base" per il tipo "{dati.tipo}"'),
        rifila_s=_numero_o_400(costanti.rifila_s, f'"Rifila" per il tipo "{dati.tipo}"'),
        sfrido_su_lunghezza_percento=costanti.sfrido_su_lunghezza_percento or 0.0,
        peso_linguetta_g=costanti.peso_linguetta_g,
        ha_linguetta=costanti.ha_linguetta,
        sormonto_disco_manuale=costanti.sormonto_disco_manuale,
        sormonto_disco_costante=costanti.sormonto_disco_costante,
        sfrido_parete_convex_d=costanti.sfrido_parete_convex_d,
        larghezza_fascia_da_dividere=costanti.larghezza_fascia_da_dividere or 1000.0,
        massa_per_superficie_parete=_numero_o_400(materiale_parete.massa_per_superficie, f'Il peso a superficie del materiale "{materiale_parete.nome}"'),
        fasce_disponibili_mm=fasce_mm,
        fascia_fissa_mm=materiale_parete.fascia_fissa_mm,
        densita_colore_g_m2=densita_colore,
        linguetta_scelta=dati.linguetta,
        diametro_disco_testa=_numero_o_400(costanti_disco.diametro_disco_testa, f'Il diametro disco per il tipo "{tipo_disco_riferimento}"'),
        massa_per_superficie_disco=_numero_o_400(materiale_disco.massa_per_superficie, f'Il peso a superficie del materiale disco "{materiale_disco.nome}"'),
    )

    try:
        return calcolo.calcola(ingresso)
    except ValueError as errore:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(errore)) from None


@router.post("/calcola", response_model=CalcoloOut)
def calcola_peso(dati: CalcoloIn, db: Session = Depends(get_db), _u: TokenPayload = Depends(_richiede_accesso)):
    return risolvi_e_calcola(db, dati)
