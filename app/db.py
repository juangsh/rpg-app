import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Se DATABASE_URL existir (ex: produção), usa ela
# Caso contrário, usa SQLite local (dev)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./rpg.db"
)

# Força SQLite no Disk do Render
if DATABASE_URL.startswith("sqlite"):
    if os.getenv("RENDER"):
        DATABASE_URL = "sqlite:////var/data/rpg.db"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
