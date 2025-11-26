from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from datetime import datetime
from typing import List

from src.config import settings
from src.infrastructure.middleware.cors_utils import add_cors_headers
from src.application.services.session_service import SessionService


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.session_service = SessionService()
    
    async def dispatch(self, request: Request, call_next):
        # Allow CORS preflight requests to pass through without auth
        # Browsers send HTTP OPTIONS requests as CORS preflight; these
        # must not be rejected with 401 since they contain no Authorization header.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for public routes
        print("PUBLIC_ROUTES", settings.PUBLIC_ROUTES)
        if request.url.path in settings.PUBLIC_ROUTES:
            return await call_next(request)
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )
            return add_cors_headers(response, request)
        
        # Check Bearer scheme
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
                return add_cors_headers(response, request)
        except ValueError:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"}
            )
            return add_cors_headers(response, request)
        
        # Verify JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id is None:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token payload"}
                )
                return add_cors_headers(response, request)
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has expired"}
                )
                return add_cors_headers(response, request)
            
            # Check if token exists in Redis (session validation)
            is_valid = await self.session_service.is_token_valid(token)
            if not is_valid:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been invalidated or session expired"}
                )
                return add_cors_headers(response, request)
            
            # Add user info to request state
            request.state.user_id = user_id
            request.state.user_payload = payload
            
        except JWTError as e:
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Invalid token: {str(e)}"}
            )
            return add_cors_headers(response, request)
        
        # Proceed to the route handler
        response = await call_next(request)
        return response
