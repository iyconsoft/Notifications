import httpx, json, time, logging
from typing import Optional, Dict, Any, Callable, List  # Added List import
from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt, jwk
from functools import wraps
from src.utils.helpers import (build_error_response, unauthorizedErrorMessage )

class KeycloakClient:

    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str):
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.public_key_cache = {}
        
    async def get_public_key(self, kid: str = None) -> Optional[Dict]:
        """Fetch public key from Keycloak for token verification"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/certs", timeout=10.0)
                if response.status_code == 200:
                    certs_data = response.json()
                    keys = certs_data.get("keys", [])
                    
                    if not keys:
                        logging.error("No public keys found in Keycloak response")
                        return None
                    
                    # Cache all keys
                    for key in keys:
                        self.public_key_cache[key.get("kid")] = key
                    
                    # Return specific key if kid provided, otherwise first key
                    if kid and kid in self.public_key_cache:
                        return self.public_key_cache[kid]
                    elif keys:
                        return keys[0]  # Return first key as default
                        
        except httpx.RequestError as e:
            logging.error(f"Network error fetching public key: {e}")
            return None
        except Exception as e:
            logging.error(f"Error fetching public key: {e}")
            return None
        return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token using Keycloak's public key
        Returns decoded token payload if valid
        """
        try:
            # First, decode token header without verification to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logging.error("Token header missing key ID (kid)")
                return None
            
            # Get the correct public key for this token
            public_key_jwk = await self.get_public_key(kid)
            if not public_key_jwk:
                logging.error(f"Public key not found for kid: {kid}")
                return None
            
            # Convert JWK to RSA public key
            try:
                # Use jose library to handle JWK to RSA conversion
                key = jwk.construct(public_key_jwk)
                public_key = key.to_pem().decode('utf-8') if hasattr(key, 'to_pem') else key
            except Exception as e:
                logging.error(f"Error constructing public key from JWK: {e}")
                # Fallback: try to use the JWK directly
                public_key = public_key_jwk
            
            # Decode and verify token
            decoded = jwt.decode(
                token,
                public_key,
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
        current_time = time.time()
        if payload.get('exp', 0) < current_time:
            logging.error(f"Token has expired. Exp: {payload.get('exp')}, Current: {current_time}")
            return False
        
        # Check audience
        aud = payload.get('aud')
        if isinstance(aud, str):
            if aud != self.client_id:
                logging.error(f"Token audience mismatch: {aud} != {self.client_id}")
                return False
        elif isinstance(aud, list):
            if self.client_id not in aud:
                logging.error(f"Token audience doesn't contain client_id: {aud}")
                return False
                
        return True

    async def get_user_groups_admin_api(self, token: str, user_id: str) -> List[Dict]:
        """Get user groups using Keycloak Admin API"""
        try:
            from src.core.config import (settings)
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"{settings.onboardingapi_url}v1/internal/onboarding/users?user_id={user_id}",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    groups = response.json()
                    logging.info(f"Found {len(groups)} groups for user {user_id}")
                    return groups[0]
                else:
                    logging.error(f"Failed to fetch organisations")
                    return []
                    
        except Exception as e:
            logging.error(f"Error fetching user groups: {e}")
            return []
    
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Keycloak userinfo endpoint"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo", headers=headers, timeout=10.0)

                if response.status_code == 200:
                    user_info = response.json()
                    # Get groups using admin API (requires additional permissions)
                    user_id = user_info.get('sub')
                    if user_id:
                        groups = await self.get_user_groups_admin_api(token, user_id)
                        if groups:
                            user_info['organizations'] = groups
                    
                    return user_info
                else:
                    logging.error(f"Userinfo endpoint returned {response.status_code}: {response.text}")
                    return None
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
            try:
                response = await client.post(
                    f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/revoke",
                    data=data,
                    timeout=10.0
                )
                return response.status_code == 200
            except Exception as e:
                logging.error(f"Error revoking token: {e}")
                return False
    
    async def introspect_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Alternative: Use token introspection endpoint (requires client credentials)"""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "token": token,
                "token_type_hint": "access_token"
            }
            try:
                response = await client.post(
                    f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token/introspect",
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logging.error(f"Error introspecting token: {e}")
        return None



class KeycloakMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, keycloak_client: KeycloakClient, exclude_paths: List = None):
        super().__init__(app)
        self.keycloak_client = keycloak_client
        self.exclude_paths = exclude_paths or []
    
    async def dispatch(self, request: Request, call_next):
        request_path = request.url.path
        
        # Skip authentication for excluded paths
        for excluded in self.exclude_paths:
            if request_path.startswith(excluded.rstrip('/')):
                return await call_next(request)
        
        # Get Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return build_error_response(
                unauthorizedErrorMessage, 403
                # data={
                #     "verbose_message": "Missing Authorization header",
                #     "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                # }
            )
        
        if not auth_header.startswith("Bearer "):
            return build_error_response(
                unauthorizedErrorMessage, 401
                # data={
                #     "verbose_message": "Invalid Authorization header. Use 'Bearer <token>' format",
                #     "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                # }
            )
        
        # Extract token
        token_parts = auth_header.split(" ")
        if len(token_parts) != 2:
            return build_error_response(
                unauthorizedErrorMessage, 401
                # data={
                #     "verbose_message": "Malformed Authorization header",
                #     "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                # }
            )
        
        token = token_parts[1]
        if not token or len(token) < 10:  # Basic sanity check
            return build_error_response(
                unauthorizedErrorMessage, 401
                # data={
                #     "verbose_message": "Invalid token",
                #     "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                # }
            )
        
        # Verify token
        token_payload = await self.keycloak_client.verify_token(token)
        if not token_payload:
            # Try introspection as fallback
            introspect_result = await self.keycloak_client.introspect_token(token)
            if introspect_result and introspect_result.get("active"):
                token_payload = {
                    "sub": introspect_result.get("sub"),
                    "preferred_username": introspect_result.get("preferred_username"),
                    "email": introspect_result.get("email"),
                    "realm_access": {"roles": introspect_result.get("realm_access", {}).get("roles", [])},
                    "resource_access": introspect_result.get("resource_access", {}),
                    "introspected": True
                }
            else:
                return build_error_response(
                    unauthorizedErrorMessage, 401
                    # data={
                    #     "verbose_message": "Invalid or expired token",
                    #     "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                    # }
                )
        
        # Get additional user info (optional)
        user_info = None
        try:
            user_info = await self.keycloak_client.get_user_info(token)
        except Exception as e:
            logging.error(f"Could not fetch user info (non-critical): {e}")
        
        # Store token and user info in request.state
        request.state.access_token = token
        request.state.token_payload = token_payload
        request.state.user_info = user_info or token_payload
        
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
            
            # Check args
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Check kwargs
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            # If using FastAPI dependency injection, request might be in context
            if not request:
                try:
                    from contextvars import ContextVar
                    import fastapi
                    request = kwargs.get('request') or args[0] if args else None
                except:
                    pass
            
            if not request or not isinstance(request, Request):
                # Try to get request from FastAPI context
                try:
                    from fastapi import Request as FastAPIRequest
                    import inspect
                    # Get the calling function's frame
                    frame = inspect.currentframe()
                    while frame:
                        local_req = frame.f_locals.get('request')
                        if isinstance(local_req, FastAPIRequest):
                            request = local_req
                            break
                        frame = frame.f_back
                except:
                    pass
            
            if not request:
                return build_error_response("Request object not found in function arguments", status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Check if authenticated via middleware
            if not hasattr(request.state, 'access_token'):
                # logging.error("No access_token in request.state - middleware may not be configured correctly")
                return build_error_response(unauthorizedErrorMessage, status.HTTP_401_UNAUTHORIZED)
            
            # Check roles if required
            if required_roles:
                user_info = getattr(request.state, 'user_info', {})
                
                # Get roles from different possible locations
                user_roles = []
                
                # Try realm_access first
                if 'realm_access' in user_info and 'roles' in user_info['realm_access']:
                    user_roles = user_info['realm_access']['roles']
                # Try resource_access
                elif 'resource_access' in user_info:
                    for resource, access in user_info['resource_access'].items():
                        if 'roles' in access:
                            user_roles.extend(access['roles'])
                # Try direct roles field
                elif 'roles' in user_info:
                    user_roles = user_info['roles']
                
                logging.info(f"User roles: {user_roles}, Required roles: {required_roles}")
                
                if not any(role in user_roles for role in required_roles):
                    return build_error_response("access denied. forbidden access", status.HTTP_403_FORBIDDEN)
            
            # Check scopes if required
            if required_scopes:
                token_payload = getattr(request.state, 'token_payload', {})
                token_scopes = token_payload.get('scope', '').split()
                
                if not any(scope in token_scopes for scope in required_scopes):
                    return build_error_response("access denied. forbidden access", status.HTTP_403_FORBIDDEN)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

