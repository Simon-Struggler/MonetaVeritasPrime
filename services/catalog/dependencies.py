from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from config import settings

def get_current_user_id_optional(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        return None