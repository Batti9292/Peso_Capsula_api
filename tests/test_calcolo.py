"""Prove su app/calcolo.py — SOLO numeri finti (mai un valore vero del
foglio Excel, per lo stesso motivo per cui models.py nasce senza dati:
Marco, 15 settembre 2026, "anche il foglio Excel è sensibile").

Ogni prova ricalcola il pezzo di formula con `math` direttamente nel
test, invece di scrivere un numero atteso a mano: il rischio vero qui
non è "la trigonometria è sbagliata" (è libreria standard), è "ho
trascritto la formula del foglio in un ordine diverso da quello vero" —
un confronto contro lo stesso calcolo scritto in modo indipendente lo
scoprirebbe."""

import math

import pytest

from app.calcolo import InputCalcolo, calcola, diametro_disco_di_riferimento, fascia_materiale_utilizzata


def _dati(**extra) -> InputCalcolo:
    valori = dict(
        tipo="capsuloni",
        diametro_testa=34.0,
        conicita_1a=8.0,
        altezza_capsula=30.0,
        altezza_testa_ht=3.0,
        sormonto_base_b=1.5,
        rifila_s=2.0,
        sfrido_su_lunghezza_percento=5.0,
        peso_linguetta_g=0.032128,
        ha_linguetta=True,
        sormonto_disco_manuale=1.0,
        massa_per_superficie_parete=0.6,
        fasce_disponibili_mm=(30.0, 35.0, 40.0, 50.0),
        densita_colore_g_m2=0.0,
        linguetta_scelta=False,
        diametro_disco_testa=30.0,
        massa_per_superficie_disco=0.5,
    )
    valori.update(extra)
    return InputCalcolo(**valori)


# ---------------------------------------------------------------------
# Geometria — ricalcolata indipendentemente con `math`
# ---------------------------------------------------------------------

def test_conicita_e_angolo_foglia_in_gradi_e_radianti():
    r = calcola(_dati(conicita_1a=8.0))
    attesa_gradi = (180 / math.pi) * math.atan(0.5 / 8.0)
    assert r.conicita_gradi == pytest.approx(attesa_gradi)
    assert r.conicita_rad == pytest.approx(attesa_gradi * math.pi / 180)
    attesa_alfa = math.sin(2 * (math.pi / 360) * attesa_gradi) * 360
    assert r.angolo_foglia_gradi == pytest.approx(attesa_alfa)
    assert r.angolo_foglia_rad == pytest.approx(attesa_alfa * math.pi / 180)


def test_raggio_foglia_usa_altezza_testa_e_semidiametro():
    r = calcola(_dati(altezza_capsula=30.0, altezza_testa_ht=3.0, diametro_testa=34.0, conicita_1a=8.0))
    conicita_rad = r.conicita_rad
    atteso = (30.0 - 3.0) / math.cos(conicita_rad) + (34.0 / 2) / math.sin(conicita_rad)
    assert r.raggio_foglia_mm == pytest.approx(atteso)


def test_sormonto_parete_beta_e_sormonto_base_diviso_raggio_foglia():
    r = calcola(_dati(sormonto_base_b=1.5))
    assert r.sormonto_parete_beta_rad == pytest.approx(1.5 / r.raggio_foglia_mm)
    assert r.sormonto_parete_beta_gradi == pytest.approx(r.sormonto_parete_beta_rad * 180 / math.pi)


def test_altezza_foglia_usa_seno_di_alfa_piu_beta():
    r = calcola(_dati())
    atteso = r.raggio_foglia_mm * math.sin(r.angolo_foglia_rad + r.sormonto_parete_beta_rad)
    assert r.altezza_foglia_mm == pytest.approx(atteso)


def test_fascia_ottimale_e_rifila_piu_altezza_foglia():
    r = calcola(_dati(rifila_s=2.0))
    assert r.fascia_ottimale_mm == pytest.approx(2.0 + r.altezza_foglia_mm)


# ---------------------------------------------------------------------
# Sormonto disco — manuale per capsuloni/convex, calcolato per gli altri
# ---------------------------------------------------------------------

def test_capsuloni_usa_il_sormonto_disco_manuale_cosi_com_e():
    r = calcola(_dati(tipo="capsuloni", sormonto_disco_manuale=1.75))
    assert r.sormonto_disco_mm == 1.75


def test_convex_usa_il_sormonto_disco_manuale_cosi_com_e():
    r = calcola(_dati(tipo="convex", sormonto_disco_manuale=2.25, sfrido_parete_convex_d=0.5))
    assert r.sormonto_disco_mm == 2.25


def test_futura_calcola_il_sormonto_disco_dalla_costante():
    r = calcola(_dati(
        tipo="futura", sormonto_disco_manuale=None, sormonto_disco_costante=1.5,
        diametro_testa=34.0, diametro_disco_testa=30.0,
    ))
    assert r.sormonto_disco_mm == pytest.approx((34.0 - 30.0) / 2 + 1.5)


def test_pvc_calcola_il_sormonto_disco_dalla_costante():
    r = calcola(_dati(
        tipo="pvc", sormonto_disco_manuale=None, sormonto_disco_costante=3.5,
        diametro_testa=34.0, diametro_disco_testa=28.0,
    ))
    assert r.sormonto_disco_mm == pytest.approx((34.0 - 28.0) / 2 + 3.5)


def test_capsuloni_senza_sormonto_manuale_solleva_un_errore_chiaro():
    with pytest.raises(ValueError, match="capsuloni"):
        calcola(_dati(tipo="capsuloni", sormonto_disco_manuale=None))


def test_futura_senza_sormonto_costante_solleva_un_errore_chiaro():
    with pytest.raises(ValueError, match="futura"):
        calcola(_dati(tipo="futura", sormonto_disco_manuale=None, sormonto_disco_costante=None))


def test_tipo_sconosciuto_solleva_un_errore_chiaro():
    with pytest.raises(ValueError, match="sconosciuto"):
        calcola(_dati(tipo="non-esiste"))


# ---------------------------------------------------------------------
# La stranezza replicata di proposito: PET legge il diametro disco di PVC
# ---------------------------------------------------------------------

def test_pet_punta_al_diametro_disco_di_pvc_non_al_proprio():
    assert diametro_disco_di_riferimento("pet") == "pvc"
    for tipo in ("capsuloni", "convex", "futura", "pvc"):
        assert diametro_disco_di_riferimento(tipo) == tipo


# ---------------------------------------------------------------------
# Passo — solo Convex aggiunge lo sfrido parete
# ---------------------------------------------------------------------

def test_passo_capsuloni_e_altezza_piu_sormonto_disco():
    r = calcola(_dati(tipo="capsuloni", altezza_capsula=30.0, sormonto_disco_manuale=1.75))
    assert r.passo_mm == pytest.approx(30.0 + 1.75)


def test_passo_convex_aggiunge_anche_lo_sfrido_parete():
    r = calcola(_dati(tipo="convex", altezza_capsula=30.0, sormonto_disco_manuale=1.75, sfrido_parete_convex_d=0.6))
    assert r.passo_mm == pytest.approx(30.0 + 1.75 + 0.6)


def test_convex_senza_sfrido_parete_solleva_un_errore_chiaro():
    with pytest.raises(ValueError, match="convex"):
        calcola(_dati(tipo="convex", sormonto_disco_manuale=1.0, sfrido_parete_convex_d=None))


# ---------------------------------------------------------------------
# fascia_materiale_utilizzata — arrotonda per eccesso, mai per difetto
# ---------------------------------------------------------------------

@pytest.mark.parametrize("ottimale,attesa", [
    (10.0, 30.0),  # più stretta di tutte -> la più stretta disponibile
    (30.0, 30.0),  # esatta -> quella stessa
    (32.0, 35.0),  # fra due -> la superiore
    (999.0, 999.0),  # più larga di tutte -> nessun arrotondamento, resta l'ottimale
])
def test_fascia_materiale_utilizzata_arrotonda_per_eccesso(ottimale, attesa):
    assert fascia_materiale_utilizzata(ottimale, (30.0, 35.0, 40.0, 50.0), None) == attesa


def test_fascia_materiale_utilizzata_non_dipende_dallordine_della_tupla():
    assert fascia_materiale_utilizzata(32.0, (50.0, 30.0, 40.0, 35.0), None) == 35.0


def test_fascia_fissa_sostituisce_del_tutto_la_scala():
    assert fascia_materiale_utilizzata(10.0, (30.0, 35.0), 999.0) == 999.0


def test_fascia_materiale_utilizzata_senza_scala_configurata_ripiega_sullottimale():
    assert fascia_materiale_utilizzata(12.3, (), None) == 12.3


# ---------------------------------------------------------------------
# Pesi — area, peso parete/disco/colore/linguetta, e il totale
# ---------------------------------------------------------------------

def test_area_360_e_peso_foglia_parete():
    r = calcola(_dati(massa_per_superficie_parete=0.6))
    area_360_attesa = math.pi * (r.raggio_foglia_mm**2 - (r.raggio_foglia_mm - r.passo_mm) ** 2)
    assert r.area_parete_360_mm2 == pytest.approx(area_360_attesa)
    area_foglia_attesa = area_360_attesa * (r.angolo_foglia_gradi + r.sormonto_parete_beta_gradi) / 360
    assert r.area_foglia_parete_mm2 == pytest.approx(area_foglia_attesa)
    peso_atteso = area_foglia_attesa * (0.6 * 1000 / 1_000_000)
    assert r.peso_foglia_parete_g == pytest.approx(peso_atteso)


def test_area_disco_e_peso_disco():
    r = calcola(_dati(diametro_disco_testa=30.0, massa_per_superficie_disco=0.5))
    area_attesa = math.pi * (30.0 / 2) ** 2
    assert r.area_disco_mm2 == pytest.approx(area_attesa)
    assert r.peso_disco_g == pytest.approx(area_attesa * (0.5 * 1000 / 1_000_000))


def test_nessun_colore_pesa_zero():
    r = calcola(_dati(densita_colore_g_m2=0.0))
    assert r.peso_colore_g == 0.0


def test_peso_colore_usa_area_disco_piu_area_foglia_parete():
    r = calcola(_dati(densita_colore_g_m2=120.0))
    atteso = 120.0 * (r.area_disco_mm2 + r.area_foglia_parete_mm2) / 1_000_000
    assert r.peso_colore_g == pytest.approx(atteso)


def test_linguetta_non_scelta_non_pesa_anche_se_il_tipo_la_permette():
    r = calcola(_dati(tipo="capsuloni", ha_linguetta=True, linguetta_scelta=False, peso_linguetta_g=0.032128))
    assert r.peso_linguetta_g == 0.0


def test_linguetta_scelta_pesa_il_valore_di_costante():
    r = calcola(_dati(tipo="capsuloni", ha_linguetta=True, linguetta_scelta=True, peso_linguetta_g=0.032128))
    assert r.peso_linguetta_g == 0.032128


def test_convex_non_ha_mai_linguetta_anche_se_richiesta():
    # Convex/Futura non hanno la riga "presenza linguetta" nel foglio.
    r = calcola(_dati(tipo="convex", sormonto_disco_manuale=1.0, sfrido_parete_convex_d=0.5, ha_linguetta=False, linguetta_scelta=True))
    assert r.peso_linguetta_g == 0.0


def test_peso_capsula_e_la_somma_di_parete_disco_colore_linguetta():
    r = calcola(_dati(tipo="capsuloni", ha_linguetta=True, linguetta_scelta=True, densita_colore_g_m2=80.0))
    assert r.peso_capsula_g == pytest.approx(r.peso_foglia_parete_g + r.peso_disco_g + r.peso_colore_g + r.peso_linguetta_g)


def test_capsuloni_somma_colore_e_linguetta_invece_di_moltiplicarli():
    """La correzione del bug trovato nel foglio originale (vedi il
    commento in cima a calcolo.py): F63 lì moltiplica invece di
    sommare. Qui deve sommare, esattamente come pvc/pet."""
    senza_linguetta = calcola(_dati(tipo="capsuloni", ha_linguetta=True, linguetta_scelta=False, densita_colore_g_m2=80.0))
    con_linguetta = calcola(_dati(tipo="capsuloni", ha_linguetta=True, linguetta_scelta=True, densita_colore_g_m2=80.0, peso_linguetta_g=0.032128))
    # Se moltiplicasse ancora, aggiungere la linguetta cambierebbe il
    # peso del colore (lo schiaccerebbe quasi a zero); sommando, la
    # differenza fra i due totali è ESATTAMENTE il peso della linguetta.
    assert con_linguetta.peso_capsula_g - senza_linguetta.peso_capsula_g == pytest.approx(0.032128)
    assert con_linguetta.peso_colore_g == senza_linguetta.peso_colore_g


# ---------------------------------------------------------------------
# Peso_Capsula_api#6 — un valore impossibile dà un peso negativo, senza
# nessun errore. Gli schemi di PATCH ora rifiutano gt=0 in scrittura
# (vedi test_riferimenti.py), ma queste sono le difese DENTRO calcola():
# l'ultima rete contro un valore già sbagliato in tabella da prima
# della correzione, o arrivato per un'altra via.
# ---------------------------------------------------------------------

def test_baseline_positiva_non_solleva_niente():
    """Da verificare al contrario: se una qualunque delle prove sotto
    smettesse di sollevare, sarebbe perché questa baseline (tutti i
    valori sensati) ha smesso di produrre un peso positivo."""
    r = calcola(_dati())
    assert r.peso_capsula_g > 0


def test_conicita_zero_solleva_valueerror_non_zerodivisionerror():
    """Prima della correzione: ZeroDivisionError non gestito, il
    servizio si rompeva invece di rispondere 400."""
    with pytest.raises(ValueError, match="conicità"):
        calcola(_dati(conicita_1a=0.0))


def test_diametro_testa_negativo_da_un_peso_negativo_bloccato():
    with pytest.raises(ValueError, match="peso non valido"):
        calcola(_dati(diametro_testa=-34.0))


def test_altezza_capsula_negativa_da_un_peso_negativo_bloccato():
    with pytest.raises(ValueError, match="peso non valido"):
        calcola(_dati(altezza_capsula=-30.0))


def test_massa_per_superficie_parete_negativa_da_un_peso_negativo_bloccato():
    with pytest.raises(ValueError, match="peso non valido"):
        calcola(_dati(massa_per_superficie_parete=-0.6))
