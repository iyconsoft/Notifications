from src.core.config import settings
from uuid import uuid4
import httpx, json
from copy import deepcopy

class ERPService:
    url: str = settings.odoo_url
    headers = settings.odoo_headers
    _base_payload: dict = settings.odoo_payload


    @staticmethod
    def _get_payload():
        """Return a fresh copy of the base payload"""
        return deepcopy(ERPService._base_payload)

    @staticmethod
    async def _request_to_erp(payload):
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=10),
                transport=httpx.AsyncHTTPTransport(retries=3)) as client:
                
                response = await client.request(
                    "POST",
                    ERPService.url,
                    headers=ERPService.headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.ConnectError as e:
            error_msg = (
                f"Connection failed to {ERPService.url}. "
                f"Possible causes:\n"
                f"- DNS resolution failed\n"
                f"- Network connectivity issues\n"
                f"- Invalid URL\n"
                f"- Service unavailable\n"
                f"Original error: {str(e)}"
            )
            raise Exception(error_msg)
            
        except httpx.TimeoutException as e:
            raise Exception(f"Request timed out after 30 seconds to {ERPService.url}")
            
        except httpx.HTTPStatusError as e:
            error_msg = (
                f"HTTP error {e.response.status_code} from {ERPService.url}\n"
                f"Response: {e.response.text[:500]}"  # Show first 500 chars of response
            )
            raise Exception(error_msg)
            
        except ValueError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")
            
        except Exception as e:
            raise Exception(f"Unexpected error calling {ERPService.url}: {str(e)}")

    @staticmethod
    async def create(model, _payload):
        try:
            payload = ERPService._get_payload()
            payload['params']['args'].extend([
                model,
                "create",
                [_payload]
            ])   
            return await ERPService._request_to_erp(payload)

        except Exception as e:
            raise Exception(str(e))