import httpx
from src.core import ( logging, settings )
from typing import Any, Dict

class ERPService:
    """ERP Provider Implementation"""
    
    def __init__(self):
        self.headers = settings.odoo_headers
        self.headers["x-api-key"] = settings.api_key
        self.headers["Connection"] = "keep-alive"
        self.url = settings.odoo_url
        self.payload =  {
            "jsonrpc": "2.0", 
            "method": "call", 
            "params": {
                "service": "object", 
                "method": "execute",
                "args": [ f"{settings.odoo_db}", f"{settings.odoo_uid}", f"{settings.odoo_api_key}", "", "", "" ]
            }
        }

    def generate_payload(self, model: str, action: str, payload):
        form = self.payload
        form['params']['args'][3] = model
        form['params']['args'][4] = action
        form['params']['args'][5] = payload
        return form

    
    async def make_request(self, payload):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{self.url}", 
                    json=payload, 
                    headers=self.headers
                )
                resp.raise_for_status()
                response = resp.json() if resp.content else {}
                if 'error' in response.keys():
                    raise Exception(response['error'])

                return response['result'] if 'result' in response.keys() else {}
            
        except Exception as e:
            raise Exception(str(e))
    
    async def send_request(self, model: str, action: str, payload: Any) -> dict:
        payload = self.generate_payload(model, action, payload)
        return await self.make_request(payload)

            