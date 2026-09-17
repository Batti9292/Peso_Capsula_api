"""Riempie `diametro_testa` e `conicita` su `formati_mandrino` coi valori
veri del foglio "dbformati mandrini dt0" (gruppo formati mandrini + testa
+ conicità.xlsx, Marco, 17 settembre 2026).

Al primo seed (05c7a2df5757) la tabella era stata popolata con solo
`gruppo`+`codice`: i due campi di geometria sono sempre stati NULL. I
valori qui sotto sono presi dal foglio, arrotondati a 4 decimali (oltre
quella precisione sono solo rumore del calcolo Excel a catena), e
abbinati per `codice` — la stessa chiave unica già in tabella, non un
nuovo elenco: una riga del foglio che non trova corrispondenza in
`formati_mandrino` viene segnalata, mai inserita come riga nuova (i
formati nascono solo dal configuratore/da una migrazione dedicata).

Uso:
    venv/Scripts/python.exe scripts/importa_geometria_mandrini.py            (solo report, non scrive nulla)
    venv/Scripts/python.exe scripts/importa_geometria_mandrini.py --scrivi   (applica gli UPDATE)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import FormatoMandrino  # noqa: E402

# codice -> (diametro_testa, conicita), dal foglio "dbformati mandrini dt0".
GEOMETRIA = [
    ("F-Ø27,9-TP-1:38", 27.8489, 37.1259),
    ("F-Ø28,6-TS-1:38", 28.5093, 38.5538),
    ("F-Ø29 -TS-1:35", 28.8881, 34.5655),
    ("F-Ø28,9-TS-1:38", 28.8493, 38.5538),
    ("F-Ø29,2 -TP-1:42", 29.0761, 41.4215),
    ("F-Ø29,5-TS-1:35", 29.0481, 34.5655),
    ("F-Ø29,23-TS-1:35", 29.1099, 34.0952),
    ("F-Ø29,25-TS-1:35", 29.1099, 34.0952),
    ("F-Ø29,5-TS VB-1:42", 29.2401, 41.7667),
    ("F-Ø29,75-TS-1:35", 29.3426, 36.0576),
    ("F-Ø29,75-TS GIR-1:32", 29.6013, 32.5455),
    ("F-Ø29,9-TS-1:34", 29.6677, 33.4133),
    ("F-Ø29,8-TP-1:35", 29.7481, 34.5655),
    ("F-Ø30,2-TP-1:35", 30.1481, 34.5655),
    ("F-Ø30,3-TS-1:30", 30.1587, 30.9383),
    ("F-Ø30,85-TS-1:35", 30.7003, 35.2958),
    ("F-Ø31,10-TS-1:41", 31.022, 41.082),
    ("F-Ø31,4-TS-1:40", 31.2675, 39.1562),
    ("F-Ø31,8-TS-1:40", 31.6675, 39.1562),
    ("F-Ø32-TS-1:32", 31.7513, 32.5455),
    ("F-Ø32,1-TS-1:40", 32.0075, 39.1562),
    ("F-Ø32,5-TS-1:35", 32.1955, 91.1273),
    ("F-Ø32,06-TP-1:30", 31.9987, 30.9383),
    ("F-Ø33-TS-1:40", 32.8679, 40.748),
    ("F-Ø33,2-TS-1:35", 33.0422, 34.8056),
    ("F-Ø33,3-TS-1:35", 33.1881, 34.5655),
    ("F-Ø35,9-TS-1:20", 35.6599, 20.4571),
    ("C-Ø29,6-1:10,8", 29.0604, 10.7994),
    ("C-Ø30,25-TP-1:6", 30.097, 6.0),
    ("C-Ø30,25-TP-1:7,5", 30.126, 7.5),
    ("C-Ø30,6-1:10", 30.0244, 9.98),
    ("C-Ø30,6-1:6", 29.574, 5.988),
    ("C-Ø30,6-1:8", 29.8244, 7.9872),
    ("C-Ø31,5-1:9", 30.8308, 8.9767),
    ("C-Ø33-1:10", 32.3732, 10.4603),
    ("C-Ø33-1:6", 32.0028, 6.0761),
    ("C-Ø34-1:10", 33.23, 10.42),
    ("C-Ø34-1:10 (853)", 33.9474, 10.4167),
    ("C-Ø34-1:6,88", 33.8184, 6.79),
    ("C-Ø34-1:6,78 FER", 33.0328, 6.7843),
    ("C-Ø34-1:7,2", 33.34, 6.9156),
    ("C-Ø34-1:8", 33.9192, 8.09),
    ("C-Ø34-1:8 ZON", 33.1388, 7.9745),
    ("C-Ø34-1:9,5", 33.5916, 9.542),
    ("C-Ø34-1:9,5 COL", 33.3012, 9.5394),
    ("C-Ø35,2-1:12,5", 34.63, 12.5),
    ("C-Ø35-1:12", 34.517, 12.0259),
    ("C-Ø35,5-1:7,15", 34.4959, 7.15),
    ("C-Ø35,6-1:10 COL", 34.909, 10.5),
    ("X-Ø34-(3°)-1:9,55", 33.55, 9.5402),
    ("X-Ø34-(3,6°)-1:7,95", 33.433, 7.9479),
    ("X-Ø34-(4°)-1:7,15", 33.3529, 7.15),
    ("X-Ø34-(4,36°)-1:6,5", 33.2826, 6.5582),
    ("M-ø38-5,25°-h165", 37.4392, 5.4466),
    ("M-ø38-5,25°-h90", 37.4392, 5.4466),
    ("M-ø38-4,5°-h185", 37.5528, 6.3532),
    ("M-ø38-4,5°-h90", 37.5528, 6.3532),
    ("M-ø42-6,25°-h200", 41.0908, 4.9652),
    ("M-ø42-6,25°-h190", 41.0908, 4.9652),
    ("M-ø47-7,2°-h205", 45.3472, 3.9588),
    ("M-ø47-7,2°-h185", 45.3472, 3.9588),
    ("M-ø47-7,2°-h230", 45.3472, 3.9588),
    ("P-Ø27,7-TP-1:25", 27.7417, 25.2335),
    ("P-Ø28-TS-1:25", 28.0, 24.2126),
    ("P-Ø29,25-TP-1:25", 29.1462, 26.1042),
    ("P-Ø29,8-TS-1:25", 29.5284, 24.81),
    ("P-Ø30-TF-1:32", 29.7806, 31.7),
    ("P-Ø30-TP-1:25", 30.06, 25.06),
    ("P-Ø30-TS-1:25", 29.84, 22.3252),
    ("P-Ø30,5-TP-1:25", 30.4992, 24.9664),
    ("P-Ø30,5-TS-1:25", 30.3367, 24.4936),
    ("P-Ø30-TS-1:28", 29.6884, 27.2206),
    ("P-Ø30,7-KLU-1:16", 30.19, 16.65),
    ("P-Ø30,8-TS-1:25", 30.8072, 22.8597),
    ("P-Ø31-TP-1:25", 30.96, 23.43),
    ("P-Ø31-TS-1:25", 30.82, 21.9825),
    ("P-Ø31,2-TP-1:20", 31.19, 20.6149),
    ("P-Ø31,3-TS-1:25", 31.14, 21.7676),
    ("P-Ø31,5-TP-1:25", 31.5671, 25.5226),
    ("P-Ø32-TP-1:25", 31.9659, 23.4069),
    ("P-Ø32-TS-1:25", 31.786, 22.8858),
    ("P-Ø32,3-KLU-1:22", 31.5923, 21.7913),
    ("P-Ø32,5-TP-1:20", 32.2372, 20.2097),
    ("P-Ø32,6-TP-1:25", 32.5375, 26.1042),
    ("P-Ø32,5-TS-1:25", 32.2444, 24.5235),
    ("P-Ø33-COL-1:25", 32.8672, 24.5686),
    ("P-Ø33-FIO-1:25", 32.8701, 24.5536),
    ("P-Ø33-MAR-1:25", 32.8072, 24.5686),
    ("P-Ø33-TP-1:25", 32.96, 24.69),
    ("P-Ø33-TS-1:25", 32.7684, 23.7958),
    ("P-Ø33,2-TV-1:25", 32.9732, 25.6368),
    ("P-Ø33,4-MAR-1:25", 33.2522, 25.2494),
    ("P-Ø33,4-TS-1:30", 33.2583, 30.012),
    ("P-Ø33,4-TV-1:30", 33.2592, 29.4175),
    ("P-Ø33,5-TF-1:25", 33.2375, 24.9508),
    ("P-Ø33,5-TP-1:25", 33.4661, 22.6659),
    ("P-Ø33,7-TS-1:25", 33.4845, 22.2879),
    ("P-Ø34-TP-1:25", 33.6177, 24.1106),
    ("P-Ø34-TS-1:25", 33.75, 22.6531),
    ("P-Ø34,3 -TP-1:20", 34.193, 20.5726),
    ("P-Ø35-TP-1:25", 34.9521, 24.7506),
    ("P-Ø35-TS-1:25", 34.7096, 25.1701),
    ("P-Ø35,5-DEN-1:22", 34.98, 22.0),
    ("P-Ø36-TF-1:20", 35.66, 19.89),
    ("P-Ø36-TP-1:25", 36.0327, 24.5837),
    ("P-Ø36,5-TP-1:25", 36.5228, 24.9975),
    ("P-Ø37-TS-1:25", 36.928, 25.0287),
    ("P-Ø37,2-TS-1:25", 37.0691, 24.3301),
    ("P-Ø38,8-TS-1:17", 38.354, 17.0187),
    ("P-Ø40,2-TP-1:25", 40.1836, 25.06),
]


def prepara_operazioni(db):
    """Ritorna (da_aggiornare, non_trovati) senza scrivere nulla —
    da_aggiornare è una lista di (riga, testa_nuovo, conicita_nuovo,
    testa_vecchio, conicita_vecchio)."""
    da_aggiornare = []
    non_trovati = []
    for codice, testa, conicita in GEOMETRIA:
        riga = db.query(FormatoMandrino).filter(FormatoMandrino.codice == codice).one_or_none()
        if riga is None:
            non_trovati.append(codice)
            continue
        if riga.diametro_testa != testa or riga.conicita != conicita:
            da_aggiornare.append((riga, testa, conicita, riga.diametro_testa, riga.conicita))
    return da_aggiornare, non_trovati


def main() -> None:
    scrivi = "--scrivi" in sys.argv
    db = SessionLocal()
    try:
        da_aggiornare, non_trovati = prepara_operazioni(db)

        print(f"Righe nel foglio: {len(GEOMETRIA)}")
        print(f"Da aggiornare: {len(da_aggiornare)}")
        for riga, testa, conicita, testa_vecchio, conicita_vecchio in da_aggiornare:
            print(f"  {riga.codice!r}: testa {testa_vecchio} -> {testa}, conicita {conicita_vecchio} -> {conicita}")

        if non_trovati:
            print(f"\nATTENZIONE: {len(non_trovati)} codici del foglio non esistono in formati_mandrino (NON toccati):")
            for codice in non_trovati:
                print(f"  {codice!r}")

        if not scrivi:
            print("\n(solo report — rilancia con --scrivi per applicare)")
            return

        for riga, testa, conicita, _, _ in da_aggiornare:
            riga.diametro_testa = testa
            riga.conicita = conicita
        db.commit()
        print(f"\nApplicato: {len(da_aggiornare)} righe aggiornate.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
