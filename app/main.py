from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .db import Base, engine, SessionLocal
from .routers import auth, player, master, cards
from .seed import seed_users  # 👈 ADICIONADO

app = FastAPI()

# Cria tabelas
Base.metadata.create_all(bind=engine)

# 👇 SEED AUTOMÁTICO (Render / Free-safe)
try:
    db = SessionLocal()
    seed_users(db)
    db.commit()
finally:
    db.close()

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers
app.include_router(auth.router)
app.include_router(player.router)
app.include_router(master.router)
app.include_router(cards.router)

# ✅ Rota raiz para não dar 404 no Render
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login")
