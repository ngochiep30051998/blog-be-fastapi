from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from datetime import datetime
from typing import List

from src.config import settings


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for public routes
        if request.url.path in settings.PUBLIC_ROUTES:
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )
        
        # Check Bearer scheme
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )
        
        # Verify JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            
            if user_id is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token payload"}
                )
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has expired"}
                )
            
            # Add user info to request state
            request.state.user_id = user_id
            request.state.user_payload = payload
            
        except JWTError as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(e)}"}
            )
        
        # Proceed to the route handler
        response = await call_next(request)
        return response
