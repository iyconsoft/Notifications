from base64 import b64decode
import httpx, asyncio
from typing import Optional, Dict, Any, Callable
from fastapi import FastAPI, Request, HTTPException, Request, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from functools import wraps

from src.core.config import settings
from src.utils.helpers.error_types import *
from src.utils.helpers.error_messages import *
from src.utils.helpers.api_responses import build_error_response

class KeycloakClient:
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str):
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.userinfo_url = f"{server_url}/realms/{realm}/protocol/openid-connect/userinfo"
        self.certs_url = f"{server_url}/realms/{realm}/protocol/openid-connect/certs"
        self.public_key = None
        
    async def get_public_key(self) -> Optional[str]:
        """Fetch public key from Keycloak for token verification"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.certs_url)
                if response.status_code == 200:
                    keys = response.json().get("keys", [])
                    if keys:
                        # Usually the first key is the one we want
                        return self._construct_public_key(keys[0])
        except Exception as e:
            logging.error(f"Error fetching public key: {e}")
        return None
    
    def _construct_public_key(self, key_info: Dict) -> str:
        """Construct RSA public key from JWK format"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        # For simplicity, using jose library which handles this internally
        # In production, you might want to use cryptography library directly
        return key_info
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token using Keycloak's public key
        Returns decoded token payload if valid
        """
        try:
            # Get public key if not cached
            if not self.public_key:
                self.public_key = await self.get_public_key()
                if not self.public_key:
                    logging.error("Failed to fetch public key")
                    return None
            
            # Decode and verify token
            decoded = jwt.decode(
                token,
                self.public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"{self.server_url}/realms/{self.realm}"
            )
            
            # Additional validation
            if not self._validate_token_claims(decoded):
                return None
                
            return decoded
            
        except JWTError as e:
            logging.error(f"JWT validation error: {e}")
            return None
        except Exception as e:
            logging.error(f"Token verification error: {e}")
            return None
    
    def _validate_token_claims(self, payload: Dict) -> bool:
        """Validate required token claims"""
        required_claims = ['exp', 'iat', 'iss', 'aud', 'sub']
        for claim in required_claims:
            if claim not in payload:
                logging.error(f"Missing required claim: {claim}")
                return False
        
        # Check if token is expired
        from time import time
        if payload.get('exp', 0) < time():
            logging.error("Token has expired")
            return False
            
        return True
    
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Keycloak userinfo endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(self.userinfo_url, headers=headers)
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logging.error(f"Error fetching user info: {e}")
        return None
        
    async def deactivate(self, access_token: str):
        """Logout/revoke token"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": access_token,
            }
            response = await client.post(
                f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/revoke",
                data=data
            )
            return response.status_code == 200



class KeycloakMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, keycloak_client: KeycloakClient, exclude_paths: list = None):
        super().__init__(app)
        self.keycloak_client = keycloak_client
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next):
        request_path = request.url.path.rstrip('/')
        
        # Skip authentication for excluded paths
        if any(request_path == path.rstrip('/') for path in self.exclude_paths):
            return await call_next(request)
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return build_error_response(
                unauthorizedErrorMessage, 401,
                data={
                    "verbose_message": "Missing or invalid Authorization header. Use 'Bearer <token>' format",
                    "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                }
            )
        
        # Extract token
        token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else ""
        if not token:
            return build_error_response(
                unauthorizedErrorMessage, 401,
                data={
                    "verbose_message": "Token not provided",
                    "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                }
            )
        
        # Verify token
        token_payload = await self.keycloak_client.verify_token(token)
        if not token_payload:
            return build_error_response(
                unauthorizedErrorMessage, 401,
                data={
                    "verbose_message": "Invalid or expired token",
                    "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                }
            )
        
        # Get additional user info if needed
        user_info = await self.keycloak_client.get_user_info(token)
        
        # Store token and user info in request.state
        request.state.access_token = token
        request.state.token_payload = token_payload
        request.state.user_info = user_info or token_payload  # Fallback to token payload
        
        response = await call_next(request)
        return response



def auth_required(
    required_roles: Optional[List[str]] = None,
    required_scopes: Optional[List[str]] = None
):
    """
    Decorator for protecting routes with authentication
    
    Usage:
        @app.get("/protected")
        @auth_required()
        async def protected_route(request: Request):
            return {"message": "Protected"}
        
        @app.get("/admin")
        @auth_required(required_roles=["admin"])
        async def admin_route(request: Request):
            return {"message": "Admin only"}
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            # Check if authenticated via middleware
            if not hasattr(request.state, 'access_token'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            
            # Check roles if required
            if required_roles:
                user_info = getattr(request.state, 'user_info', {})
                user_roles = user_info.get('realm_access', {}).get('roles', [])
                
                if not any(role in user_roles for role in required_roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required roles: {required_roles}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

