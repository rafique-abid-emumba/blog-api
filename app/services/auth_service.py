import logging
import time
from datetime import timedelta
from fastapi import HTTPException, status
from app.core.security import (
    create_access_token, create_refresh_token, verify_refresh_token,
)
from app.core.token_blacklist import is_token_blacklisted, blacklist_token

logger = logging.getLogger(__name__)

def issue_tokens(user_id: str, role: str) -> dict:
    access_token = create_access_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(minutes=30)
    )
    refresh_token = create_refresh_token(
        data={"sub": user_id, "role": role},
        expires_delta=timedelta(days=7)
    )
    logger.info(f"Issued new access and refresh tokens for user_id={user_id}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def blacklist_refresh_token_with_payload(refresh_token: str, payload: dict, user_id: str):
    try:
        exp = payload.get("exp")
        now = int(time.time())
        if exp is not None:
            expires_in = max(exp - now, 0)
            blacklist_token(refresh_token, expires_in)
            logger.info(f"Refresh token blacklisted for user_id={user_id}")
        else:
            logger.warning("No exp in refresh token payload; skipping blacklist TTL")
    except Exception as e:
        logger.error(f"Failed to blacklist refresh token: {e}")

def refresh_user_token(refresh_token: str) -> dict:
    try:
        if is_token_blacklisted(refresh_token):
            logger.warning("Attempt to use blacklisted refresh token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has been revoked")
        payload = verify_refresh_token(refresh_token)
        if not payload:
            logger.warning("Invalid refresh token used")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or not role:
            logger.warning("Refresh token payload missing sub or role")
            raise HTTPException(status_code=400, detail="Invalid token payload")
        tokens = issue_tokens(user_id, role)
        blacklist_refresh_token_with_payload(refresh_token, payload, user_id)
        return tokens
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh_user_token: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh token") 