from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.security import verify_access_token

api_key_header = APIKeyHeader(name="Authorization")

def get_current_user(token: str = Depends(api_key_header)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload 