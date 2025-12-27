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


def _is_https(request: Request) -> bool:
    """
    Render fica atrás de proxy. O esquema real costuma vir em X-Forwarded-Proto.
    """
    xf_proto = request.headers.get("x-forwarded-proto")
    if xf_proto:
        return xf_proto.split(",")[0].strip().lower() == "https"
    return request.url.scheme.lower() == "https"


def set_session(request: Request, response: Response, user_id: int):
    token = serializer.dumps({"user_id": user_id})

    secure_cookie = _is_https(request)

    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=secure_cookie,         # ✅ Render: True | Local: False
        max_age=60 * 60 * 24 * 14,
        path="/",
    )


def clear_session(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


def read_session(request: Request, max_age_seconds: int = 60 * 60 * 24 * 14):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        return data.get("user_id")
    except BadSignature:
        return None
