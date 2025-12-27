import os
from dotenv import load_dotenv

load_dotenv()

APP_SECRET = os.getenv("APP_SECRET")
if not APP_SECRET:
    raise RuntimeError("APP_SECRET não definido")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # fallback apenas para DEV local
    DATABASE_URL = "sqlite:///./rpg.db"
