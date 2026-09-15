"""Il calcolo del peso di una capsula — porta in Python le formule del
foglio "Peso Capsula" / " Disco" (letto il 15 settembre 2026, solo
formule ed etichette, mai i numeri veri — vedi models.py).

Funzioni PURE: nessun accesso al database qui dentro. Il router risolve
formato/materiali/costanti dal database e passa qui solo numeri, così
la geometria si può provare senza un database in mezzo.

--------------------------------------------------------------------
UNA STRANEZZA TROVATA NEL FOGLIO ORIGINALE, corretta qui di proposito
--------------------------------------------------------------------
Il "peso capsula totale" di Capsuloni nel foglio è:
    F63 = F54 + F58 + F61*F62   (peso_parete + peso_disco + peso_colore*peso_linguetta)
mentre PVC e PET (gli altri due tipi con linguetta) fanno:
    O63 = O54 + O58 + O61 + O41*O62   (... + peso_colore + presenza_linguetta*peso_linguetta)
Capsuloni MOLTIPLICA il peso del colore per il peso della linguetta
invece di sommare il contributo della linguetta come fanno pvc/pet —
quasi certamente un errore di trascinamento della formula nel foglio
originale (le unità non tornano: g × g invece di g + g), non una
scelta voluta. Qui si usa per TUTTI i tipi con linguetta la stessa
regola di pvc/pet (sommare, non moltiplicare) — da confermare con
Marco, ma tenere l'errore avrebbe voluto dire portarselo dietro nel
software nuovo sapendo che è sbagliato.
--------------------------------------------------------------------

ALTRA STRANEZZA, replicata così com'è (non un errore evidente, potrebbe
essere voluto): il "sormonto disco" e l'"area disco" di PET si calcolano
sul diametro disco di PVC, non sul proprio (' Disco'!R17 e R56 leggono
entrambi $K$2, la cella di PVC, mai $M$2 che sarebbe quella di PET) —
vedi `_DIAMETRO_DISCO_DI_RIFERIMENTO` sotto. Da confermare con Marco se
è voluto (stesso disco fisico per pvc e pet) o un altro trascinamento
sbagliato."""

from __future__ import annotations

import math
from dataclasses import dataclass

TIPI_CON_SORMONTO_DISCO_MANUALE = ("capsuloni", "convex")
TIPI_CON_SORMONTO_DISCO_CALCOLATO = ("futura", "pvc", "pet")

# Vedi il commento in cima al file: pet usa il diametro disco di pvc,
# non il proprio. Tutti gli altri tipi usano il proprio.
_DIAMETRO_DISCO_DI_RIFERIMENTO = {
    "capsuloni": "capsuloni",
    "convex": "convex",
    "futura": "futura",
    "pvc": "pvc",
    "pet": "pvc",
}


def diametro_disco_di_riferimento(tipo: str) -> str:
    """Quale tipo usare per leggere il diametro disco — vedi il
    commento in cima al file per il perché "pet" non torna "pet"."""
    return _DIAMETRO_DISCO_DI_RIFERIMENTO[tipo]


@dataclass
class InputCalcolo:
    tipo: str  # uno di models.TIPI_CAPSULA

    # Dal formato mandrino scelto (FormatoMandrino)
    diametro_testa: float
    conicita_1a: float

    # Scelto liberamente da chi compila (Marco: "altezza libera")
    altezza_capsula: float

    # Dalle costanti fisse del tipo (CostantiTipoCapsula)
    altezza_testa_ht: float
    sormonto_base_b: float
    rifila_s: float
    sfrido_su_lunghezza_percento: float
    peso_linguetta_g: float
    ha_linguetta: bool
    sormonto_disco_manuale: float | None = None  # capsuloni, convex
    sormonto_disco_costante: float | None = None  # futura, pvc, pet
    sfrido_parete_convex_d: float | None = None  # solo convex
    larghezza_fascia_da_dividere: float = 1000.0  # E31/D13 nel foglio: "larghezza fascia da dividere x"

    # Dal materiale parete scelto (MaterialeParete)
    massa_per_superficie_parete: float = 0.0  # kg/m2
    fasce_disponibili_mm: tuple[float, ...] = ()  # in ordine crescente
    fascia_fissa_mm: float | None = None  # sostituisce del tutto la scala, se impostata

    # Dal colore scelto (VarianteColore) — 0 se "nessun colore"
    densita_colore_g_m2: float = 0.0

    # Se ha_linguetta e l'utente l'ha scelta per questo pezzo
    linguetta_scelta: bool = False

    # Dalle costanti disco del TIPO DI RIFERIMENTO (vedi
    # diametro_disco_di_riferimento) e dal materiale disco scelto
    diametro_disco_testa: float = 0.0
    massa_per_superficie_disco: float = 0.0  # kg/m2


@dataclass
class RisultatoCalcolo:
    # Geometria intermedia — esposta per trasparenza (così chi guarda
    # il risultato può confrontarlo col foglio riga per riga), non
    # perché serva a chi chiama.
    conicita_gradi: float
    conicita_rad: float
    angolo_foglia_gradi: float
    angolo_foglia_rad: float
    raggio_foglia_mm: float
    sormonto_parete_beta_rad: float
    sormonto_parete_beta_gradi: float
    sormonto_disco_mm: float
    altezza_foglia_mm: float
    passo_mm: float
    fascia_ottimale_mm: float
    fascia_materiale_utilizzata_mm: float
    sfrido_rifile_percento: float
    area_parete_360_mm2: float
    area_foglia_parete_mm2: float
    area_disco_mm2: float

    # Il numero che conta
    peso_foglia_parete_g: float
    peso_disco_g: float
    peso_colore_g: float
    peso_linguetta_g: float
    peso_capsula_g: float


def fascia_materiale_utilizzata(fascia_ottimale_mm: float, fasce_disponibili_mm: tuple[float, ...], fascia_fissa_mm: float | None) -> float:
    """La prima larghezza disponibile (in ordine crescente) non più
    stretta di `fascia_ottimale_mm` — mai una più stretta di quanto
    serve davvero. Se nessuna è abbastanza larga, o non ce n'è
    nessuna configurata, si usa la fascia ottimale così com'è (stesso
    ripiego dell'ultimo ramo dell'IF nel foglio originale).

    `fascia_fissa_mm` (Marco, per materiali come "STARDUST - GLITTER"
    nel foglio originale) sostituisce del tutto questa scala quando è
    impostata."""
    if fascia_fissa_mm is not None:
        return fascia_fissa_mm
    for larghezza in sorted(fasce_disponibili_mm):
        if larghezza >= fascia_ottimale_mm:
            return larghezza
    return fascia_ottimale_mm


def calcola(dati: InputCalcolo) -> RisultatoCalcolo:
    if dati.tipo in TIPI_CON_SORMONTO_DISCO_MANUALE:
        if dati.sormonto_disco_manuale is None:
            raise ValueError(f'"{dati.tipo}" richiede sormonto_disco_manuale.')
        sormonto_disco = dati.sormonto_disco_manuale
    elif dati.tipo in TIPI_CON_SORMONTO_DISCO_CALCOLATO:
        if dati.sormonto_disco_costante is None:
            raise ValueError(f'"{dati.tipo}" richiede sormonto_disco_costante.')
        # F17/O17/R17 nel foglio: (øtesta - ødisco)/2 + costante.
        sormonto_disco = (dati.diametro_testa - dati.diametro_disco_testa) / 2 + dati.sormonto_disco_costante
    else:
        raise ValueError(f'Tipo capsula sconosciuto: "{dati.tipo}".')

    # --- Geometria (F7-F19) ---
    conicita_gradi = (180 / math.pi) * math.atan(0.5 / dati.conicita_1a)
    conicita_rad = conicita_gradi * math.pi / 180
    angolo_foglia_gradi = math.sin(2 * (math.pi / 360) * conicita_gradi) * 360
    angolo_foglia_rad = angolo_foglia_gradi * math.pi / 180
    raggio_foglia = (
        (dati.altezza_capsula - dati.altezza_testa_ht) / math.cos(conicita_rad)
        + (dati.diametro_testa / 2) / math.sin(conicita_rad)
    )
    sormonto_parete_beta_rad = dati.sormonto_base_b / raggio_foglia
    sormonto_parete_beta_gradi = sormonto_parete_beta_rad * 180 / math.pi
    altezza_foglia = raggio_foglia * math.sin(angolo_foglia_rad + sormonto_parete_beta_rad)

    # --- Passo (F20) — solo Convex aggiunge lo sfrido parete ---
    passo = dati.altezza_capsula + sormonto_disco
    if dati.tipo == "convex":
        if dati.sfrido_parete_convex_d is None:
            raise ValueError('"convex" richiede sfrido_parete_convex_d.')
        passo += dati.sfrido_parete_convex_d

    # --- Fascia di materiale (F21-F25) ---
    fascia_ottimale = dati.rifila_s + altezza_foglia
    fascia_usata = fascia_materiale_utilizzata(fascia_ottimale, dati.fasce_disponibili_mm, dati.fascia_fissa_mm)
    sfrido_rifile_percento = (fascia_usata - fascia_ottimale) * 100 / fascia_usata if fascia_usata else 0.0

    # --- Pesi (F51-F63) ---
    area_360 = math.pi * (raggio_foglia**2 - (raggio_foglia - passo) ** 2)
    area_foglia_parete = area_360 * (angolo_foglia_gradi + sormonto_parete_beta_gradi) / 360
    peso_per_superficie_parete_g_mm2 = dati.massa_per_superficie_parete * 1000 / 1_000_000
    peso_foglia_parete = area_foglia_parete * peso_per_superficie_parete_g_mm2

    area_disco = math.pi * (dati.diametro_disco_testa / 2) ** 2
    peso_per_superficie_disco_g_mm2 = dati.massa_per_superficie_disco * 1000 / 1_000_000
    peso_disco = area_disco * peso_per_superficie_disco_g_mm2

    peso_colore = dati.densita_colore_g_m2 * (area_disco + area_foglia_parete) / 1_000_000

    # Marco, foglio "presenza linguetta": solo capsuloni/pvc/pet
    # possono averla — vedi il commento in cima al file sulla formula
    # "corretta" (somma, non moltiplica) usata qui per tutti.
    peso_linguetta = dati.peso_linguetta_g if (dati.ha_linguetta and dati.linguetta_scelta) else 0.0

    peso_capsula = peso_foglia_parete + peso_disco + peso_colore + peso_linguetta

    return RisultatoCalcolo(
        conicita_gradi=conicita_gradi,
        conicita_rad=conicita_rad,
        angolo_foglia_gradi=angolo_foglia_gradi,
        angolo_foglia_rad=angolo_foglia_rad,
        raggio_foglia_mm=raggio_foglia,
        sormonto_parete_beta_rad=sormonto_parete_beta_rad,
        sormonto_parete_beta_gradi=sormonto_parete_beta_gradi,
        sormonto_disco_mm=sormonto_disco,
        altezza_foglia_mm=altezza_foglia,
        passo_mm=passo,
        fascia_ottimale_mm=fascia_ottimale,
        fascia_materiale_utilizzata_mm=fascia_usata,
        sfrido_rifile_percento=sfrido_rifile_percento,
        area_parete_360_mm2=area_360,
        area_foglia_parete_mm2=area_foglia_parete,
        area_disco_mm2=area_disco,
        peso_foglia_parete_g=peso_foglia_parete,
        peso_disco_g=peso_disco,
        peso_colore_g=peso_colore,
        peso_linguetta_g=peso_linguetta,
        peso_capsula_g=peso_capsula,
    )
