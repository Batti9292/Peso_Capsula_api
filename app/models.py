"""Modelli SQLAlchemy — porta in software il foglio Excel "Peso Capsule"
che oggi Marco gestisce a mano (tab: Peso Capsula, Disco, dati parete,
dati dischi, dbformati mandrini dt0, Varianti). Letto SOLO nelle
formule/etichette (mai i numeri veri, su richiesta esplicita di Marco,
15 settembre 2026): queste tabelle nascono VUOTE nei valori numerici,
con solo la struttura (nomi/codici) che si può leggere dalle etichette
del foglio — i numeri li inserisce una persona autorizzata dalla
schermata riservata, una volta.

Marco, 15 settembre 2026: "tutte le celle modificabili ma nessuna riga
aggiungibile o togliibile — si romperebbe il calcolatore" (le
posizioni sono usate dai calcoli, tenute per NOME qui invece che per
posizione di riga come nel foglio originale, ma lo spirito è lo
stesso: niente POST/DELETE su queste tabelle, solo PATCH sui valori,
vedi routers/riferimenti.py)."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

# I 5 "tipi capsula" del foglio (una colonna ciascuno in "Peso Capsula"
# e " Disco"): usati come chiave in CostantiTipoCapsula/CostantiDiscoTipo
# e come parametro di calcolo.py — MAI un elenco libero, un tipo nuovo
# richiederebbe anche nuove formule, non solo una nuova riga.
TIPI_CAPSULA = ("capsuloni", "convex", "futura", "pvc", "pet")


class FormatoMandrino(Base):
    """Foglio "dbformati mandrini dt0" — il formato (es. "C-Ø34-1:8")
    scelto nel configuratore, con la geometria del mandrino che porta
    dietro (diametro alla testa e conicità)."""

    __tablename__ = "formati_mandrino"

    id: Mapped[int] = mapped_column(primary_key=True)
    gruppo: Mapped[str] = mapped_column(String(5), default="")
    codice: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    diametro_testa: Mapped[float | None] = mapped_column(Float, nullable=True)
    conicita: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Marco, 15 settembre 2026: un formato non ancora/non più in uso si
    # disattiva invece di cancellarlo (mai una riga tolta, vedi il
    # commento in cima al file) — sparisce dalla tendina del
    # configuratore ma resta qui coi suoi valori.
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class MaterialeParete(Base):
    """Foglio "dati parete" — un materiale di supporto (es. "COMFORT –
    12/40/12"). `massa_per_superficie` è l'unico valore che entra nel
    peso della capsula (il prezzo del foglio originale era solo
    informativo, mai usato in nessuna formula — tolto su richiesta di
    Marco, 15 settembre 2026).

    `fascia_fissa_mm`, se impostata, SOSTITUISCE del tutto la normale
    tabella delle larghezze disponibili (vedi FasciaDisponibile) per
    QUESTO materiale — nel foglio originale succede per "STARDUST -
    GLITTER" (una riga con un valore fisso invece della scala normale
    di larghezze standard)."""

    __tablename__ = "materiali_parete"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    codice_commerciale: Mapped[str] = mapped_column(String(20), default="")
    spessore_my: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Foglio "dati parete" colonna H — Batti9292/Peso_Capsula_api#7,
    # punto 3: lo spessore del SOLO alluminio dentro il polilaminato
    # (diverso da `spessore_my`, che è lo spessore totale del
    # materiale). Non ancora usato da calcolo.py: serve al blocco
    # "impiego/ordine" descritto nella stessa issue, non ancora
    # implementato — il campo per raccoglierlo fin da subito c'è.
    my_alu: Mapped[float | None] = mapped_column(Float, nullable=True)
    peso_specifico: Mapped[float | None] = mapped_column(Float, nullable=True)  # g/cm3
    massa_per_superficie: Mapped[float | None] = mapped_column(Float, nullable=True)  # kg/m2
    fascia_fissa_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class FasciaDisponibile(Base):
    """Larghezze di bobina standard disponibili, in ordine crescente,
    per tipo capsula (foglio "dati parete") — la fascia calcolata si
    arrotonda per eccesso alla prima di queste che non sia più stretta
    di quanto serve (mai a una più stretta). `ordine` fissa la
    sequenza di confronto: dev'essere crescente per `larghezza_mm`,
    ma la RIGA in sé non si può aggiungere/togliere (Marco, 15
    settembre 2026), solo modificarne il valore."""

    __tablename__ = "fasce_disponibili"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), index=True)  # uno di TIPI_CAPSULA
    ordine: Mapped[int] = mapped_column(Integer, default=0)
    larghezza_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class MaterialeDisco(Base):
    """Foglio "dati dischi" — un materiale del disco (es. "50my"),
    solo il peso per superficie: è l'unico valore usato nel calcolo del
    peso del disco."""

    __tablename__ = "materiali_disco"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    massa_per_superficie: Mapped[float | None] = mapped_column(Float, nullable=True)  # kg/m2


class VarianteColore(Base):
    """Foglio "Varianti " — due elenchi separati (colori capsula in
    PVC e in Alluminio), qui unificati con un campo `gruppo` per
    distinguerli: il configuratore mostra solo quelli del gruppo giusto
    per il materiale scelto. `densita_g_m2` è il peso aggiuntivo del
    colore per metro quadro di capsula."""

    __tablename__ = "varianti_colore"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    gruppo: Mapped[str] = mapped_column(String(20), default="pvc")  # "pvc" o "alluminio"
    densita_g_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    # Peso_Capsula_api#14 — quando `densita_g_m2` e' stata verificata
    # l'ultima volta ("questo numero e' ancora quello giusto?"). Si
    # aggiorna SOLO quando cambia la densita' (vedi
    # routers/riferimenti.py), mai al solo rinominare: altrimenti
    # smetterebbe di voler dire "verificato" e diventerebbe "toccato a
    # caso". Le righe esistenti restano NULL — nessuna data inventata.
    aggiornato_il: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CostantiTipoCapsula(Base):
    """Foglio "Peso Capsula" — le celle scritte A MANO (non da una
    formula), diverse per ognuno dei 5 tipi: una riga per tipo invece
    di una colonna, stessa cosa vista di lato. Alcuni campi valgono
    solo per certi tipi (vedi i commenti sui singoli campi) — restano
    `None` per gli altri, calcolo.py sa quali usare per quale tipo.

    `sormonto_disco_manuale` (capsuloni/convex) e
    `sormonto_disco_costante` (futura/pvc/pet) sono le due varianti
    della stessa riga del foglio ("sorm disco s"): per i primi due tipi
    è un numero scritto a mano, per gli altri tre è calcolato da una
    formula che usa il diametro del disco più una costante fissa (1.5
    per futura, 3.5 per pvc/pet) — vedi calcolo.py."""

    __tablename__ = "costanti_tipo_capsula"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # uno di TIPI_CAPSULA

    altezza_testa_ht: Mapped[float | None] = mapped_column(Float, nullable=True)
    sormonto_base_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    rifila_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    sormonto_disco_manuale: Mapped[float | None] = mapped_column(Float, nullable=True)  # capsuloni, convex
    sormonto_disco_costante: Mapped[float | None] = mapped_column(Float, nullable=True)  # futura, pvc, pet

    sfrido_parete_convex_d: Mapped[float | None] = mapped_column(Float, nullable=True)  # solo convex
    sfrido_su_lunghezza_percento: Mapped[float | None] = mapped_column(Float, nullable=True)

    larghezza_fascia_da_dividere: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Marco (foglio, riga "presenza linguetta"): capsuloni/pvc/pet
    # possono avere la linguetta, convex/futura no — il configuratore
    # nasconde l'opzione dove `ha_linguetta` è falso.
    ha_linguetta: Mapped[bool] = mapped_column(Boolean, default=False)
    peso_linguetta_g: Mapped[float] = mapped_column(Float, default=0.032128)


class CostantiDiscoTipo(Base):
    """Foglio " Disco" — le celle scritte a mano lì, una riga per tipo.
    `diametro_disco_testa` alimenta sia il peso del disco sia (per
    futura/pvc/pet) il calcolo di "sormonto disco" sul lato Capsula —
    vedi il commento su CostantiTipoCapsula.sormonto_disco_costante."""

    __tablename__ = "costanti_disco_tipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # uno di TIPI_CAPSULA

    diametro_disco_testa: Mapped[float | None] = mapped_column(Float, nullable=True)
    fascia_stampa_utilizzata: Mapped[float | None] = mapped_column(Float, nullable=True)
    passo: Mapped[float | None] = mapped_column(Float, nullable=True)
    sfrido_rifile_percento: Mapped[float | None] = mapped_column(Float, nullable=True)
    sfrido_lunghezza_percento: Mapped[float | None] = mapped_column(Float, nullable=True)


class CalcoloRegistrato(Base):
    """Storico dei calcoli salvati esplicitamente (mai sui ricalcoli
    live del Configuratore, solo quando l'utente clicca "Salva nello
    storico") — Batti9292/Peso_Capsula_api#9, stesso modello di
    lead_time_api::CalcoloRegistrato: CONDIVISO, chiunque abbia accesso
    al modulo vede i calcoli di tutti (proposta di Marco nell'issue,
    "il peso di una capsula non è un dato personale"), per questo porta
    con sé chi lo ha salvato come username in chiaro.

    Si salvano le SCELTE (nomi, non id: un materiale rinominato non deve
    far sparire il perché di un calcolo vecchio) più il RISULTATO che il
    Configuratore già mostra — mai i numeri di riferimento (diametri,
    conicità, masse): chi non ha il permesso di dettaglio non deve
    vederli riapparire dallo storico (routers/storico.py::registra_calcolo
    li ricalcola sempre da capo, non salva mai quelli mandati dal
    browser)."""

    __tablename__ = "calcoli_registrati"

    id: Mapped[int] = mapped_column(primary_key=True)
    creato_da_username: Mapped[str] = mapped_column(String(150), default="")
    creato_il: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    tipo: Mapped[str] = mapped_column(String(20), default="")  # uno di TIPI_CAPSULA
    formato_codice: Mapped[str] = mapped_column(String(50), default="")
    altezza_capsula: Mapped[float] = mapped_column(Float, default=0.0)
    materiale_parete_nome: Mapped[str] = mapped_column(String(100), default="")
    materiale_disco_nome: Mapped[str] = mapped_column(String(50), default="")
    colore_nome: Mapped[str] = mapped_column(String(100), default="")
    linguetta: Mapped[bool] = mapped_column(Boolean, default=False)

    peso_capsula_g: Mapped[float] = mapped_column(Float, default=0.0)
    peso_foglia_parete_g: Mapped[float] = mapped_column(Float, default=0.0)
    peso_disco_g: Mapped[float] = mapped_column(Float, default=0.0)
    peso_colore_g: Mapped[float] = mapped_column(Float, default=0.0)
    peso_linguetta_g: Mapped[float] = mapped_column(Float, default=0.0)
    fascia_materiale_utilizzata_mm: Mapped[float] = mapped_column(Float, default=0.0)
    sfrido_rifile_percento: Mapped[float] = mapped_column(Float, default=0.0)
