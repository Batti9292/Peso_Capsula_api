"""Schemi Pydantic. Le tabelle di riferimento (formati mandrino,
materiali, varianti colore, costanti per tipo, fasce disponibili) hanno
solo un Out e un PatchIn — MAI un CreaIn o un'eliminazione esposta
all'API: "nessuna riga aggiungibile o togliibile" (Marco, 15 settembre
2026), le righe nascono da un seed/migrazione, non da una POST."""

from pydantic import BaseModel, ConfigDict

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
    che lo cita per nome."""
    diametro_testa: float | None = None
    conicita: float | None = None
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
    codice_commerciale: str | None = None
    spessore_my: float | None = None
    my_alu: float | None = None
    peso_specifico: float | None = None
    massa_per_superficie: float | None = None
    fascia_fissa_mm: float | None = None
    attivo: bool | None = None


class MaterialeDiscoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    massa_per_superficie: float | None


class MaterialeDiscoPatchIn(BaseModel):
    massa_per_superficie: float | None = None


class VarianteColoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    gruppo: str
    densita_g_m2: float | None
    attivo: bool


class VarianteColorePatchIn(BaseModel):
    densita_g_m2: float | None = None
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
    larghezza_mm: float | None = None
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
    altezza_testa_ht: float | None = None
    sormonto_base_b: float | None = None
    rifila_s: float | None = None
    sormonto_disco_manuale: float | None = None
    sormonto_disco_costante: float | None = None
    sfrido_parete_convex_d: float | None = None
    sfrido_su_lunghezza_percento: float | None = None
    larghezza_fascia_da_dividere: float | None = None
    ha_linguetta: bool | None = None
    peso_linguetta_g: float | None = None


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
    diametro_disco_testa: float | None = None
    fascia_stampa_utilizzata: float | None = None
    passo: float | None = None
    sfrido_rifile_percento: float | None = None
    sfrido_lunghezza_percento: float | None = None


# ---- Il configuratore ----


class CalcoloIn(BaseModel):
    tipo: str  # uno di models.TIPI_CAPSULA
    formato_codice: str
    altezza_capsula: float
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
    altezza_capsula: float
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
