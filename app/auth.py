from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature
from fastapi import Request, Response
from .config import APP_SECRET

pwd = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)

serializer = URLSafeTimedSerializer(APP_SECRET, salt="rpg-session")

COOKIE_NAME = "rpg_session"

def hash_password(password: str) -> str:
    return pwd.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd.verify(password, password_hash)

def set_session(response: Response, user_id: int):
    token = serializer.dumps({"user_id": user_id})
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60*60*24*14,
    )

def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME)

def read_session(request: Request, max_age_seconds: int = 60*60*24*14):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        return data.get("user_id")
    except BadSignature:
        return None
