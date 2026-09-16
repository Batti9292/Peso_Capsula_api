from datetime import datetime, timezone
from typing import Annotated

from pydantic import PlainSerializer

# SQLite (il database di questo servizio) NON conserva il fuso orario di
# un datetime attraverso un giro di scrittura e lettura -- stesso
# difetto reale gia' trovato e corretto in lead_time_api/richiesta_
# fattibilita_api (controllo_progetto_claudeOpus, punto 1-ter): sia
# DateTime che DateTime(timezone=True) restituiscono un datetime INGENUO
# dopo una query, anche scrivendo un valore con tzinfo=UTC. La
# correzione non sta nello scrivere con datetime.now(timezone.utc)
# invece di datetime.utcnow() -- a valle di SQLite sono identici, il
# fuso e' comunque perso -- sta nel dire esplicitamente, in uscita verso
# il JSON, che quell'ora ingenua e' UTC, per convenzione: ogni orario
# scritto da questo servizio lo e' sempre, mai locale.
#
# Senza questo, `new Date(s)` nel browser legge una stringa senza fuso
# come ora LOCALE (un'eliminazione delle 23:17 appariva come 21:17,
# Marco, 10 settembre 2026, in un altro modulo).


def _con_fuso_utc(valore: datetime) -> str:
    if valore.tzinfo is None:
        valore = valore.replace(tzinfo=timezone.utc)
    return valore.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# Da usare al posto di `datetime` nei campi in USCITA (schemas *Out) che
# rappresentano un orario scritto dal server -- non per un input
# dell'utente, che non ha questo problema.
OrarioUTC = Annotated[datetime, PlainSerializer(_con_fuso_utc, return_type=str)]
