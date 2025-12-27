from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Card, User
from ..auth import read_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Canon (DB) -> Label (UI)
RARITY_OPTIONS = [
    ("comum", "Comum"),
    ("incomum", "Incomum"),
    ("rara", "Rara"),
    ("epica", "Épica"),
    ("lendaria", "Lendária"),
    ("mitica", "Mítica"),
]

CLASS_OPTIONS = [
    ("combatente", "Combatente"),
    ("potencializador", "Potencializador"),
    ("estrategico", "Estratégico"),
    ("especialista", "Especialista"),
]

TYPE_OPTIONS = [
    ("arma", "Armas"),
    ("inimigo", "Inimigos"),
    ("local", "Locais"),
]


def _get_logged_user(request: Request, db: Session) -> User | None:
    user_id = read_session(request)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/cards", response_class=HTMLResponse)
def cards_catalog(request: Request, db: Session = Depends(get_db)):
    me = _get_logged_user(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    # Query params
    rarity = (request.query_params.get("rarity") or "").strip().lower()
    sort = (request.query_params.get("sort") or "az").strip().lower()  # az | za
    card_type = (request.query_params.get("type") or "").strip().lower()  # arma|inimigo|local|"" (todos)
    class_type = (request.query_params.get("class_type") or "").strip().lower()  # apenas armas

    valid_rarities = {r[0] for r in RARITY_OPTIONS}
    valid_types = {t[0] for t in TYPE_OPTIONS}
    valid_classes = {c[0] for c in CLASS_OPTIONS}

    q = db.query(Card)

    # Se classe foi selecionada, força tipo "arma"
    if class_type in valid_classes:
        card_type = "arma"

    # Filtro por tipo
    if card_type in valid_types:
        q = q.filter(Card.type == card_type)

    # Filtro por raridade
    if rarity in valid_rarities:
        q = q.filter(Card.rarity == rarity)

    # Filtro por classe (somente armas)
    if card_type == "arma" and class_type in valid_classes:
        q = q.filter(Card.class_type == class_type)

    # Ordenação
    if sort == "za":
        q = q.order_by(Card.order_name.desc())
    else:
        q = q.order_by(Card.order_name.asc())

    cards = q.all()

    return templates.TemplateResponse(
        "cards_catalog.html",
        {
            "request": request,
            "me": me,
            "cards": cards,
            "rarity_options": RARITY_OPTIONS,
            "type_options": TYPE_OPTIONS,
            "class_options": CLASS_OPTIONS,
            "selected_rarity": rarity,
            "selected_sort": sort,
            "selected_type": card_type,
            "selected_class": class_type,
        },
    )
