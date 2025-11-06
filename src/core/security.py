from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional

from src.config import settings

security = HTTPBearer()



async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get current user from JWT token
    """
    token = credentials.credentials  # Extract token string from bearer
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
        # Optional: Check token expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
            
        return {"user_id": user_id, "payload": payload}
        
    except JWTError:
        raise credentials_exception