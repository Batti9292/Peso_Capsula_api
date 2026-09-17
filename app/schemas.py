"""Schemi Pydantic. Le tabelle di riferimento (formati mandrino,
materiali, varianti colore, costanti per tipo, fasce disponibili) hanno
solo un Out e un PatchIn — MAI un CreaIn o un'eliminazione esposta
all'API: "nessuna riga aggiungibile o togliibile" (Marco, 15 settembre
2026), le righe nascono da un seed/migrazione, non da una POST."""

from pydantic import BaseModel, ConfigDict, Field

from .fuso_orario import OrarioUTC


class FormatoMandrinoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    gruppo: str
    codice: str
    diametro_testa: float | None
    conicita: float | None
    attivo: bool


class FormatoMandrinoPatchIn(BaseModel):
    """Tutti opzionali — PATCH scrive solo i campi inviati. `codice` è
    escluso di proposito: è la chiave con cui il configuratore sceglie
    il formato, cambiarla romperebbe qualunque richiesta già salvata
    che lo cita per nome.

    Peso_Capsula_api#6: `gt=0` su diametro e conicità — un valore a
    zero o negativo qui produce un peso capsula assurdo (negativo, o
    per `conicita=0` una divisione per zero che rompe il servizio),
    riprodotto eseguendo il motore di calcolo vero."""
    diametro_testa: float | None = Field(None, gt=0)
    conicita: float | None = Field(None, gt=0)
    attivo: bool | None = None


class MaterialeParteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    codice_commerciale: str
    spessore_my: float | None
    my_alu: float | None
    peso_specifico: float | None
    massa_per_superficie: float | None
    fascia_fissa_mm: float | None
    attivo: bool


class MaterialeParetePatchIn(BaseModel):
    """Peso_Capsula_api#6: `gt=0` sui campi fisici — uno spessore, una
    densità o una massa per superficie negativa o a zero non hanno
    senso fisico e producono un peso capsula sbagliato senza nessun
    errore (misurato: -0,5070 g invece di 0,6964 g con
    `massa_per_superficie` negativa)."""
    codice_commerciale: str | None = None
    spessore_my: float | None = Field(None, gt=0)
    my_alu: float | None = Field(None, gt=0)
    peso_specifico: float | None = Field(None, gt=0)
    massa_per_superficie: float | None = Field(None, gt=0)
    fascia_fissa_mm: float | None = Field(None, gt=0)
    attivo: bool | None = None


class MaterialeDiscoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    massa_per_superficie: float | None


class MaterialeDiscoPatchIn(BaseModel):
    massa_per_superficie: float | None = Field(None, gt=0)


class VarianteColoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    gruppo: str
    densita_g_m2: float | None
    attivo: bool
    # Peso_Capsula_api#14 — None vuol dire "mai verificato", non si
    # inventa una data: a schermo va mostrato come "mai aggiornato" o
    # un trattino, mai una data odierna.
    aggiornato_il: OrarioUTC | None


class VarianteColorePatchIn(BaseModel):
    densita_g_m2: float | None = Field(None, gt=0)
    attivo: bool | None = None


class VarianteColoreNomeOut(BaseModel):
    """Solo nome+gruppo, per la tendina colore del configuratore — il
    gruppo (pvc/alluminio) serve a mostrare solo le varianti giuste
    per il materiale scelto."""
    model_config = ConfigDict(from_attributes=True)
    nome: str
    gruppo: str


class FasciaDisponibileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    ordine: int
    larghezza_mm: float | None
    attivo: bool


class FasciaDisponibilePatchIn(BaseModel):
    larghezza_mm: float | None = Field(None, gt=0)
    attivo: bool | None = None


class CostantiTipoCapsulaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    altezza_testa_ht: float | None
    sormonto_base_b: float | None
    rifila_s: float | None
    sormonto_disco_manuale: float | None
    sormonto_disco_costante: float | None
    sfrido_parete_convex_d: float | None
    sfrido_su_lunghezza_percento: float | None
    larghezza_fascia_da_dividere: float | None
    ha_linguetta: bool
    peso_linguetta_g: float


class CostantiTipoCapsulaPatchIn(BaseModel):
    """Peso_Capsula_api#6: `gt=0` sulle misure fisiche (un'altezza, un
    sormonto, una rifila o un peso a zero/negativo non hanno senso e
    producono un peso capsula sbagliato senza nessun errore — misurato
    con `altezza_testa_ht`: -0,3679 g invece di 0,6964 g). Gli sfridi
    sono percentuali che possono legittimamente essere zero (nessuno
    scarto), quindi solo `ge=0`, mai negativi.

    Peso_Capsula_api#11: quella tabella di #6 partiva da una
    configurazione INVENTATA, non dal foglio Excel vero — tre vincoli
    hanno superato il bersaglio e rifiutavano i valori VERI:
    - `altezza_testa_ht`: 0 su TUTTI e cinque i tipi -> `ge=0`.
    - `rifila_s`: 0 su Futura/PVC/PET -> `ge=0`.
    - `sormonto_disco_manuale`: è un sormonto CON SEGNO (-0,65 su
      Convex è il valore vero) -> nessun limite.
    Il calcolo con questi valori funziona (Convex 1,6946 g, Futura
    1,5481 g): non sono errori di battitura, sono la configurazione
    vera. Resta la protezione che conta — il calcolo non restituisce
    mai un peso ≤ 0 — che è in uscita, non su questi campi."""
    altezza_testa_ht: float | None = Field(None, ge=0)
    sormonto_base_b: float | None = Field(None, gt=0)
    rifila_s: float | None = Field(None, ge=0)
    sormonto_disco_manuale: float | None = None
    sormonto_disco_costante: float | None = Field(None, gt=0)
    sfrido_parete_convex_d: float | None = Field(None, gt=0)
    sfrido_su_lunghezza_percento: float | None = Field(None, ge=0)
    # "N. di fasce da dividere" (operx#152/#153): un conteggio, non una
    # misura — comunque mai zero o negativo.
    larghezza_fascia_da_dividere: float | None = Field(None, gt=0)
    ha_linguetta: bool | None = None
    peso_linguetta_g: float | None = Field(None, gt=0)


class CostantiDiscoTipoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tipo: str
    diametro_disco_testa: float | None
    fascia_stampa_utilizzata: float | None
    passo: float | None
    sfrido_rifile_percento: float | None
    sfrido_lunghezza_percento: float | None


class CostantiDiscoTipoPatchIn(BaseModel):
    """Peso_Capsula_api#6: `gt=0` su diametro/fascia/passo (misurato con
    `diametro_disco_testa`: 0,9399 g invece di 0,6964 g da negativo).
    Gli sfridi restano `ge=0`, come in CostantiTipoCapsulaPatchIn."""
    diametro_disco_testa: float | None = Field(None, gt=0)
    fascia_stampa_utilizzata: float | None = Field(None, gt=0)
    passo: float | None = Field(None, gt=0)
    sfrido_rifile_percento: float | None = Field(None, ge=0)
    sfrido_lunghezza_percento: float | None = Field(None, ge=0)


# ---- Il configuratore ----


class CalcoloIn(BaseModel):
    tipo: str  # uno di models.TIPI_CAPSULA
    formato_codice: str
    # Peso_Capsula_api#6: gt=0 — a zero/negativo produce un peso
    # sbagliato senza nessun errore (misurato: -0,3679 g invece di
    # 0,6964 g), è un valore scelto liberamente da chi compila, non
    # letto da una tabella.
    altezza_capsula: float = Field(..., gt=0)
    materiale_parete_nome: str
    materiale_disco_nome: str
    colore_nome: str | None = None
    linguetta: bool = False


class CalcoloOut(BaseModel):
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
    peso_foglia_parete_g: float
    peso_disco_g: float
    peso_colore_g: float
    peso_linguetta_g: float
    peso_capsula_g: float


# ---- Storico (Batti9292/Peso_Capsula_api#9) ----


class RegistraCalcoloIn(BaseModel):
    """Le stesse scelte di CalcoloIn — MAI un peso: il router rifà il
    calcolo da capo (routers/configuratore.py::risolvi_e_calcola) e
    salva solo il risultato che esce da lì."""
    tipo: str
    formato_codice: str
    altezza_capsula: float = Field(..., gt=0)
    materiale_parete_nome: str
    materiale_disco_nome: str
    colore_nome: str | None = None
    linguetta: bool = False


class CalcoloRegistratoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    creato_da_username: str
    creato_il: OrarioUTC

    tipo: str
    formato_codice: str
    altezza_capsula: float
    materiale_parete_nome: str
    materiale_disco_nome: str
    colore_nome: str
    linguetta: bool

    peso_capsula_g: float
    peso_foglia_parete_g: float
    peso_disco_g: float
    peso_colore_g: float
    peso_linguetta_g: float
    fascia_materiale_utilizzata_mm: float
    sfrido_rifile_percento: float
