from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..auth import verify_password, hash_password, set_session, clear_session, read_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _get_logged_user(request: Request, db: Session) -> User | None:
    user_id = read_session(request)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()

    if (not user) or (not verify_password(password, user.password_hash)):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuário ou senha incorretos."},
            status_code=401
        )

    resp = RedirectResponse(url="/me", status_code=303)

    # ✅ IMPORTANTE: agora passa request também
    set_session(request, resp, user.id)

    return resp


@router.get("/me")
def me_redirect(request: Request, db: Session = Depends(get_db)):
    user = _get_logged_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if getattr(user, "force_password_change", False):
        return RedirectResponse(url="/change-password", status_code=303)

    role = (user.role or "").strip().lower()
    if role == "master":
        return RedirectResponse(url="/master", status_code=303)

    return RedirectResponse(url="/player", status_code=303)


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(request: Request, db: Session = Depends(get_db)):
    user = _get_logged_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not getattr(user, "force_password_change", False):
        return RedirectResponse(url="/me", status_code=303)

    return templates.TemplateResponse(
        "change_password.html",
        {"request": request, "error": None}
    )


@router.post("/change-password")
def change_password_submit(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _get_logged_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not getattr(user, "force_password_change", False):
        return RedirectResponse(url="/me", status_code=303)

    new_password = (new_password or "").strip()
    confirm_password = (confirm_password or "").strip()

    if len(new_password) < 8:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "A senha deve ter pelo menos 8 caracteres."},
            status_code=400
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            "change_password.html",
            {"request": request, "error": "As senhas não conferem."},
            status_code=400
        )

    user.password_hash = hash_password(new_password)
    user.force_password_change = False
    db.commit()

    resp = RedirectResponse(url="/me", status_code=303)

    # ✅ IMPORTANTE: reemitir cookie com secure correto
    set_session(request, resp, user.id)

    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    clear_session(resp)
    return resp
