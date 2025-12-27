from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .db import Base, engine
from .routers import auth, player, master, cards


app = FastAPI()

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(player.router)
app.include_router(master.router)
app.include_router(cards.router)
