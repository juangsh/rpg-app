# app/seed.py
import os
import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from .models import User


# === Password hashing (simples e estável) ===
# Formato salvo: pbkdf2_sha256$<iters>$<salt_hex>$<hash_hex>
def hash_password(password: str, *, iterations: int = 210_000) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def _upsert_user(
    db: Session,
    *,
    username: str,
    password: str,
    role: str,
    force_password_change: bool = False,
) -> None:
    username = (username or "").strip()
    if not username:
        return

    u = db.query(User).filter(User.username == username).first()

    if u is None:
        u = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            force_password_change=force_password_change,
        )
        db.add(u)
        return

    # Se o usuário já existe, atualiza role e (se necessário) senha
    changed = False

    if u.role != role:
        u.role = role
        changed = True

    # Atualiza senha se estiver diferente
    if password and not verify_password(password, u.password_hash):
        u.password_hash = hash_password(password)
        u.force_password_change = force_password_change
        changed = True

    if changed:
        db.add(u)


def seed_users(db: Session) -> None:
    admin_user = os.getenv("SEED_ADMIN_USER", "master")
    admin_pass = os.getenv("SEED_ADMIN_PASS", "suaSenha")

    player_user = os.getenv("SEED_PLAYER_USER", "player")
    player_pass = os.getenv("SEED_PLAYER_PASS", "suaSenha")

    _upsert_user(
        db,
        username=admin_user,
        password=admin_pass,
        role="master",
        force_password_change=False,
    )
    _upsert_user(
        db,
        username=player_user,
        password=player_pass,
        role="player",
        force_password_change=False,
    )
