from base64 import b64decode
import httpx, logging
from fastapi import FastAPI, Request, HTTPException, Request, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.utils.helpers.error_types import *
from src.utils.helpers.error_messages import *
from src.utils.helpers.api_responses import build_error_response


# Updated verify_credentials to return the token and user info
class KeycloakClient:
    def __init__(self, server_url: str, realm: str, client_id: str, client_secret: str):
        self.server_url = server_url
        self.token_url = f"{server_url}/realms/{realm}/protocol/openid-connect/token"
        self.userinfo_url = (
            f"{server_url}/realms/{realm}/protocol/openid-connect/userinfo"
        )
        self.client_id = client_id
        self.client_secret = client_secret

    async def authenticate(self, username: str, password: str):
        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": username,
                "password": password,
                "scope": "openid",
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = await client.post(self.token_url, data=data, headers=headers)
            if response.status_code != 200:
                return None

            token_data = response.json()
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")

            # Optionally get user info
            headers = {"Authorization": f"Bearer {access_token}"}
            userinfo_response = await client.get(self.userinfo_url, headers=headers)
            userinfo = (
                userinfo_response.json() if userinfo_response.status_code == 200 else {}
            )

            return {
                "access_token": access_token,
                "user_info": userinfo,
                "refresh_token": refresh_token,
            }

    async def deactivate(self, access_token: str, realm: str):
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.post(
                f"{self.server_url}/realms/{realm}/protocol/openid-connect/logout",
                headers=headers,
            )
            if response.status_code != 204:
                return None
            return {"message": "User logged out successfully"}


class KeycloakMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, keycloak_client: KeycloakClient, exclude_paths: list = None):
        super().__init__(app)
        self.keycloak_client = keycloak_client
        self.exclude_paths = exclude_paths or []

    async def dispatch(self, request: Request, call_next):
        request_path = request.url.path.rstrip('/')
        
        if any(request_path == path.rstrip('/') for path in self.exclude_paths):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Basic "):
            return build_error_response(
                unauthorizedErrorMessage, 401, 
                data={
                    "verbose_message": "Missing or invalid Authorization header",
                    "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                }
            )

        try:
            encoded_credentials = auth_header.split(" ")[1]
            decoded_credentials = b64decode(encoded_credentials).decode("utf-8")
            username, password = decoded_credentials.split(":", 1)
        except Exception:
            return build_error_response(
                badRequestErrorMessage, 400, 
                data={
                    "verbose_message": "Invalid Basic Auth format",
                    "error_type": errorTypes["BAD_REQUEST"]
                }
            )

        auth_result = await self.keycloak_client.authenticate(username, password)
        if not auth_result:
            return build_error_response(
                unauthorizedErrorMessage, 401, 
                data={
                    "verbose_message": "Invalid username or password",
                    "error_type": errorTypes["UNAUTHORIZED_ACCESS"]
                }
            )

        # Store token and user info in request.state
        request.state.access_token = auth_result["access_token"]
        request.state.user_info = auth_result["user_info"]

        response = await call_next(request)
        return response


async def get_current_token(request: Request) -> str:
    token = getattr(request.state, "access_token", None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return token


async def get_current_user(request: Request) -> dict:
    user_info = getattr(request.state, "user_info", None)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User info not found"
        )
    return user_info


auth_dependency = Depends(get_current_user)
keycloak_client = KeycloakClient(
    server_url=settings.keycloak_server_url,
    realm=settings.keycloak_realm,
    client_id=settings.keycloak_client_id,
    client_secret=settings.keycloak_client_secret,
)

