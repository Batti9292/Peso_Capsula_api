from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


def abilita_foreign_keys_sqlite(motore) -> None:
    """SQLite ignora silenziosamente le ForeignKey dichiarate nei modelli
    finché non si abilita esplicitamente PRAGMA foreign_keys per ogni
    connessione — stesso pattern di ogni altro servizio della piattaforma
    (vedi cilindri_api/app/database.py per il perché)."""
    if motore.dialect.name != "sqlite":
        return

    @event.listens_for(motore, "connect")
    def _abilita(connessione_dbapi, _record):
        cursore = connessione_dbapi.cursor()
        cursore.execute("PRAGMA foreign_keys=ON")
        cursore.close()


_ATTESA_MS = 15000


def configura_sqlite(motore) -> None:
    """WAL + busy_timeout — stesso motivo di cilindri_api/app/database.py:
    un lettore non deve bloccarsi dietro uno scrittore su SQLite."""

    @event.listens_for(motore, "connect")
    def _pragma(connessione_dbapi, _record):  # pragma: no cover - chiamato da SQLAlchemy
        import sqlite3

        if not isinstance(connessione_dbapi, sqlite3.Connection):
            return
        cursore = connessione_dbapi.cursor()
        cursore.execute("PRAGMA journal_mode=WAL")
        cursore.execute(f"PRAGMA busy_timeout={_ATTESA_MS}")
        cursore.close()


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
abilita_foreign_keys_sqlite(engine)
configura_sqlite(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseNonPronto(RuntimeError):
    pass


def verifica_database_pronto(motore=None, url: str | None = None) -> None:
    """Rifiuta di avviare il servizio se il database non ha lo schema —
    stesso controllo (e stessa ragione) di ogni altro servizio della
    piattaforma: vedi cilindri_api/app/database.py per i dettagli."""
    import os

    from sqlalchemy import inspect

    motore = motore if motore is not None else engine
    url = url if url is not None else DATABASE_URL

    tabelle = set(inspect(motore).get_table_names())
    mancanti = {"formati_mandrino", "materiali_parete"} - tabelle
    if not mancanti:
        return

    dove = url
    if url.startswith("sqlite:///"):
        dove = url[len("sqlite:///"):]

    raise DatabaseNonPronto(
        f"Il database non contiene le tabelle della piattaforma (mancano: {', '.join(sorted(mancanti))})."
        f"\n\nDatabase in uso:\n    {dove}"
        + ("\n(preso dal default, perche' DATABASE_URL non e' configurata)"
           if not os.environ.get("DATABASE_URL") else "")
        + "\n\nSe e' la PRIMA installazione, crea lo schema:"
        "\n    venv/Scripts/alembic upgrade head"
    )
