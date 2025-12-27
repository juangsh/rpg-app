from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import secrets
import string

from ..db import get_db
from ..models import User, Character
from ..auth import read_session, hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# =========================
# Helpers
# =========================
def _require_master(request: Request, db: Session) -> User | None:
    user_id = read_session(request)
    if not user_id:
        return None
    me = db.query(User).filter(User.id == user_id).first()
    if not me or (me.role or "").lower() != "master":
        return None
    return me


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# =========================
# Dashboard
# =========================
@router.get("/master", response_class=HTMLResponse)
def master_dashboard(request: Request, db: Session = Depends(get_db)):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    players = (
        db.query(User)
        .filter(User.role == "player")
        .order_by(User.id.asc())
        .all()
    )

    return templates.TemplateResponse(
        "master_dashboard.html",
        {
            "request": request,
            "me": me,
            "players": players,
            "error": None,
            "success": None,
        },
    )


# =========================
# Criar jogador
# =========================
@router.post("/master/create-player")
def create_player(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    username = username.strip()
    if not username:
        return RedirectResponse(url="/master", status_code=303)

    existing = db.query(User).filter(User.username == username).first()
    if existing:
        players = db.query(User).filter(User.role == "player").order_by(User.id.asc()).all()
        return templates.TemplateResponse(
            "master_dashboard.html",
            {
                "request": request,
                "me": me,
                "players": players,
                "error": "Esse username já existe. Escolha outro.",
                "success": None,
            },
            status_code=400,
        )

    user = User(
        username=username,
        password_hash=hash_password(password),
        role="player",
        force_password_change=True,
    )
    db.add(user)
    db.flush()  # obtém user.id

    # cria personagem inicial
    c = Character(user_id=user.id, name=username.upper())
    db.add(c)
    db.commit()

    return RedirectResponse(url="/master", status_code=303)


# =========================
# Excluir jogador
# =========================
@router.post("/master/delete-player/{user_id}")
def delete_player(user_id: int, request: Request, db: Session = Depends(get_db)):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/master", status_code=303)

    if (user.role or "").lower() != "player":
        players = db.query(User).filter(User.role == "player").order_by(User.id.asc()).all()
        return templates.TemplateResponse(
            "master_dashboard.html",
            {
                "request": request,
                "me": me,
                "players": players,
                "error": "Apenas usuários com role=player podem ser excluídos.",
                "success": None,
            },
            status_code=400,
        )

    db.query(Character).filter(Character.user_id == user.id).delete()
    db.delete(user)
    db.commit()

    return RedirectResponse(url="/master", status_code=303)


# =========================
# Reset de senha do jogador
# =========================
@router.post("/master/reset-password/{user_id}")
def reset_player_password(user_id: int, request: Request, db: Session = Depends(get_db)):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user or (user.role or "").lower() != "player":
        return RedirectResponse(url="/master", status_code=303)

    temp_password = _generate_temp_password()

    user.password_hash = hash_password(temp_password)
    user.force_password_change = True
    db.commit()

    players = db.query(User).filter(User.role == "player").order_by(User.id.asc()).all()

    return templates.TemplateResponse(
        "master_dashboard.html",
        {
            "request": request,
            "me": me,
            "players": players,
            "error": None,
            "success": f"Senha de {user.username} resetada. Nova senha temporária: {temp_password}",
        },
    )
