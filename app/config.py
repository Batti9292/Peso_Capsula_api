import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'peso_capsula.db'}")
DEBUG = os.environ.get("DEBUG", "True") == "True"
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

# Deve combaciare con AppRegistrata.nome nell'Auth Service.
NOME_APP = "Peso Capsula"
