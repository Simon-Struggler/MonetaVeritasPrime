from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from config import settings

def get_current_user_id(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(401, "Invalid token")

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(401, "Invalid token")

    token = parts[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(401, "Invalid token")
        return user_id
    except JWTError as e:
        # Для отладки: можно залогировать e
        raise HTTPException(401, "Invalid token")