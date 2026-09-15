"""Peso Capsula API — modulo nuovo di zecca. Porta in software il
foglio Excel "Peso Capsule" (letto il 15 settembre 2026 SOLO nelle
formule/etichette, mai i numeri veri — vedi models.py e calcolo.py per
i dettagli e le stranezze trovate nel foglio originale). Database
separato, non condiviso con nessun altro servizio."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from .config import CORS_ORIGINS
from .database import verifica_database_pronto
from .errori import interpreta_violazione
from .routers import configuratore, riferimenti

logger = logging.getLogger(__name__)

MESSAGGIO_ERRORE_IMPREVISTO = "Errore imprevisto del modulo. Riprova; se succede ancora, dillo a Claudio."


@asynccontextmanager
async def _ciclo_di_vita(_app: FastAPI):
    verifica_database_pronto()
    yield


app = FastAPI(title="Peso Capsula API", version="0.1.0", lifespan=_ciclo_di_vita)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
def _violazione_di_vincolo(_richiesta: Request, errore: IntegrityError) -> JSONResponse:
    codice, messaggio = interpreta_violazione(str(errore.orig))
    return JSONResponse(status_code=codice, content={"detail": messaggio})


@app.exception_handler(Exception)
def _errore_imprevisto(richiesta: Request, errore: Exception) -> JSONResponse:
    logger.error("Errore non gestito su %s %s", richiesta.method, richiesta.url.path, exc_info=errore)
    return JSONResponse(status_code=500, content={"detail": MESSAGGIO_ERRORE_IMPREVISTO})


app.include_router(riferimenti.router)
app.include_router(configuratore.router)


@app.get("/")
def radice():
    return {"servizio": "peso-capsula-api", "stato": "ok"}
