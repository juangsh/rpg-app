from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .db import get_db
from .auth import read_session
from .models import User

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = read_session(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

def require_master(user: User = Depends(get_current_user)) -> User:
    if user.role != "master":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user
