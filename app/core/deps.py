from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.security import verify_access_token

api_key_header = APIKeyHeader(name="Authorization")

def get_current_user(token: str = Depends(api_key_header)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload

# RBAC dependency
def require_role(required_roles: list):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user["role"] not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker 