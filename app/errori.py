"""Come rispondere quando il database rifiuta una scrittura — stesso
schema di ogni altro servizio della piattaforma (vedi
cilindri_api/app/errori.py per il perché di questo file)."""

import re

_UNICO = re.compile(r"UNIQUE constraint failed:\s*(?P<colonne>[\w.,\s]+)")

NOMI: dict[str, str] = {
    "formati_mandrino": "un formato mandrino",
    "materiali_parete": "un materiale parete",
    "materiali_disco": "un materiale disco",
    "varianti_colore": "una variante colore",
    "fasce_disponibili": "una fascia disponibile",
    "costanti_tipo_capsula": "una riga di costanti",
    "costanti_disco_tipo": "una riga di costanti disco",
}


def _campi(colonne: str) -> list[str]:
    return [pezzo.strip().split(".")[-1] for pezzo in colonne.split(",") if pezzo.strip()]


def _tabella(colonne: str) -> str:
    primo = colonne.split(",")[0].strip()
    return primo.split(".")[0] if "." in primo else ""


def interpreta_violazione(testo: str) -> tuple[int, str]:
    unico = _UNICO.search(testo)
    if unico:
        colonne = unico.group("colonne")
        cosa = NOMI.get(_tabella(colonne), "una voce")
        campi = _campi(colonne)
        if len(campi) == 1:
            return 409, f"Esiste gia' {cosa} con questo valore di «{campi[0]}»."
        if campi:
            return 409, f"Esiste gia' {cosa} con questa combinazione di {', '.join(f'«{c}»' for c in campi)}."
        return 409, f"Esiste gia' {cosa} con questi valori."

    if "FOREIGN KEY constraint failed" in testo:
        return 400, "Il riferimento indicato non esiste (o e' stato eliminato nel frattempo)."

    if "NOT NULL constraint failed" in testo:
        return 400, "Manca un dato obbligatorio."

    return 409, "La richiesta e' in conflitto con i dati gia' presenti."
