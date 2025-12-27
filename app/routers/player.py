from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User, Character
from ..auth import read_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_logged_user(request: Request, db: Session) -> User | None:
    user_id = read_session(request)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def _require_master(request: Request, db: Session) -> User | None:
    me = _get_logged_user(request, db)
    if not me:
        return None
    if (me.role or "").lower() != "master":
        return None
    return me


def _get_or_create_character(db: Session, user: User) -> Character:
    c = db.query(Character).filter(Character.user_id == user.id).first()
    if not c:
        c = Character(user_id=user.id, name=(user.username or "").upper())
        db.add(c)
        db.commit()
        db.refresh(c)
    return c


def _clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def _apply_character_form(c: Character, form: dict) -> None:
    # Campos texto
    name = (form.get("name") or "").strip()
    age = (form.get("age") or "").strip()
    occupation = (form.get("occupation") or "").strip()
    level = (form.get("level") or "").strip()
    affiliation = (form.get("affiliation") or "").strip()
    personality = (form.get("personality") or "hero").strip()

    if name:
        c.name = name
    c.age = age
    c.occupation = occupation
    if level:
        c.level = level
    c.affiliation = affiliation
    c.personality = personality if personality in ("hero", "antihero", "villain") else "hero"

    # Atributos numéricos
    c.heroism = _clamp(int(form.get("heroism", 50)), 1, 100)
    c.agility = _clamp(int(form.get("agility", 50)), 1, 100)
    c.intellect = _clamp(int(form.get("intellect", 50)), 1, 100)
    c.strength = _clamp(int(form.get("strength", 50)), 1, 100)
    c.willpower = _clamp(int(form.get("willpower", 50)), 1, 100)
    c.vigor = _clamp(int(form.get("vigor", 50)), 1, 100)

    c.hp = _clamp(int(form.get("hp", 25)), 0, 999)
    c.hero_points = _clamp(int(form.get("hero_points", 5)), 0, 999)

    c.notes = form.get("notes", "") or ""
    c.inventory_text = form.get("inventory_text", "") or ""
    c.skills_text = form.get("skills_text", "") or ""


@router.get("/player", response_class=HTMLResponse)
def player_sheet(request: Request, db: Session = Depends(get_db)):
    me = _get_logged_user(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    # Se for mestre, direciona para o painel dele (evita UX confusa)
    if (me.role or "").lower() == "master":
        return RedirectResponse(url="/master", status_code=303)

    c = _get_or_create_character(db, me)

    return templates.TemplateResponse(
        "player_sheet.html",
        {"request": request, "user": me, "c": c, "error": None, "show_back": False},
    )


@router.post("/player/update")
def player_update(
    request: Request,
    db: Session = Depends(get_db),

    name: str = Form(""),
    age: str = Form(""),
    occupation: str = Form(""),
    level: str = Form(""),
    affiliation: str = Form(""),
    personality: str = Form("hero"),

    heroism: int = Form(50),
    agility: int = Form(50),
    intellect: int = Form(50),
    strength: int = Form(50),
    willpower: int = Form(50),
    vigor: int = Form(50),

    hp: int = Form(25),
    hero_points: int = Form(5),

    notes: str = Form(""),
    inventory_text: str = Form(""),
    skills_text: str = Form(""),
):
    me = _get_logged_user(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    # Mestre não deveria usar esse endpoint
    if (me.role or "").lower() == "master":
        return RedirectResponse(url="/master", status_code=303)

    c = _get_or_create_character(db, me)

    _apply_character_form(
        c,
        {
            "name": name,
            "age": age,
            "occupation": occupation,
            "level": level,
            "affiliation": affiliation,
            "personality": personality,
            "heroism": heroism,
            "agility": agility,
            "intellect": intellect,
            "strength": strength,
            "willpower": willpower,
            "vigor": vigor,
            "hp": hp,
            "hero_points": hero_points,
            "notes": notes,
            "inventory_text": inventory_text,
            "skills_text": skills_text,
        },
    )

    db.commit()
    return RedirectResponse(url="/player", status_code=303)


# Mestre visualizar ficha de um jogador específico
@router.get("/player/{user_id}", response_class=HTMLResponse)
def player_sheet_for_master(user_id: int, request: Request, db: Session = Depends(get_db)):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user or (user.role or "").lower() != "player":
        return RedirectResponse(url="/master", status_code=303)

    c = _get_or_create_character(db, user)

    return templates.TemplateResponse(
        "player_sheet.html",
        {"request": request, "user": user, "c": c, "error": None, "show_back": True},
    )


# Mestre atualizar ficha de um jogador específico (endpoint separado e explícito)
@router.post("/player/{user_id}/update")
def player_update_for_master(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),

    name: str = Form(""),
    age: str = Form(""),
    occupation: str = Form(""),
    level: str = Form(""),
    affiliation: str = Form(""),
    personality: str = Form("hero"),

    heroism: int = Form(50),
    agility: int = Form(50),
    intellect: int = Form(50),
    strength: int = Form(50),
    willpower: int = Form(50),
    vigor: int = Form(50),

    hp: int = Form(25),
    hero_points: int = Form(5),

    notes: str = Form(""),
    inventory_text: str = Form(""),
    skills_text: str = Form(""),
):
    me = _require_master(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user or (user.role or "").lower() != "player":
        return RedirectResponse(url="/master", status_code=303)

    c = _get_or_create_character(db, user)

    _apply_character_form(
        c,
        {
            "name": name,
            "age": age,
            "occupation": occupation,
            "level": level,
            "affiliation": affiliation,
            "personality": personality,
            "heroism": heroism,
            "agility": agility,
            "intellect": intellect,
            "strength": strength,
            "willpower": willpower,
            "vigor": vigor,
            "hp": hp,
            "hero_points": hero_points,
            "notes": notes,
            "inventory_text": inventory_text,
            "skills_text": skills_text,
        },
    )

    db.commit()
    return RedirectResponse(url=f"/player/{user_id}", status_code=303)
@router.post("/player/{user_id}/update")
def player_update_for_master(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),

    name: str = Form(""),
    age: str = Form(""),
    occupation: str = Form(""),
    level: str = Form(""),
    affiliation: str = Form(""),
    personality: str = Form("hero"),

    heroism: int = Form(50),
    agility: int = Form(50),
    intellect: int = Form(50),
    strength: int = Form(50),
    willpower: int = Form(50),
    vigor: int = Form(50),

    hp: int = Form(25),
    hero_points: int = Form(5),

    notes: str = Form(""),
    inventory_text: str = Form(""),
    skills_text: str = Form(""),
):
    me = _get_logged_user(request, db)
    if not me:
        return RedirectResponse(url="/login", status_code=303)
    if (me.role or "").lower() != "master":
        return RedirectResponse(url="/player", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/master", status_code=303)

    c = db.query(Character).filter(Character.user_id == user.id).first()
    if not c:
        c = Character(user_id=user.id, name=user.username.upper())
        db.add(c)
        db.flush()

    def clamp(v, lo, hi):
        return max(lo, min(hi, v))

    c.name = name.strip() or c.name
    c.age = age.strip()
    c.occupation = occupation.strip()
    c.level = level.strip() or c.level
    c.affiliation = affiliation.strip()
    c.personality = personality if personality in ("hero", "antihero", "villain") else "hero"

    c.heroism = clamp(int(heroism), 1, 100)
    c.agility = clamp(int(agility), 1, 100)
    c.intellect = clamp(int(intellect), 1, 100)
    c.strength = clamp(int(strength), 1, 100)
    c.willpower = clamp(int(willpower), 1, 100)
    c.vigor = clamp(int(vigor), 1, 100)

    c.hp = clamp(int(hp), 0, 999)
    c.hero_points = clamp(int(hero_points), 0, 999)

    c.notes = notes
    c.inventory_text = inventory_text
    c.skills_text = skills_text

    db.commit()
    return RedirectResponse(url=f"/player/{user_id}", status_code=303)
