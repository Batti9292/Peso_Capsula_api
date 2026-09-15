import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from battistella_auth import crea_access_token

from app.database import Base, abilita_foreign_keys_sqlite, get_db
from app.main import app

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
abilita_foreign_keys_sqlite(engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def db_pulito():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    return TestingSessionLocal()


@pytest.fixture
def client():
    return TestClient(app)


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token_utente():
    return _bearer(crea_access_token(sub="1", username="collaudo_utente", rango=1, apps=["Peso Capsula"]))


@pytest.fixture
def token_marco_miotti():
    # Stesso id (sub) hardcoded in routers/riferimenti.py::ID_MARCO_MIOTTI —
    # rango basso (Ufficio Tecnico, come nella realtà) ma vede comunque
    # le tabelle di dettaglio.
    return _bearer(crea_access_token(sub="51", username="collaudo_mm01", rango=1, apps=["Peso Capsula"], reparti=["UFFICIO TECNICO"]))


@pytest.fixture
def token_admin():
    return _bearer(crea_access_token(sub="7", username="collaudo_admin", rango=3, apps=["Peso Capsula"]))


@pytest.fixture
def token_senza_accesso():
    return _bearer(crea_access_token(sub="9", username="altro_reparto", rango=4, apps=["Lead Time"]))
