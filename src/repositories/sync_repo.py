from src.services import *
from src.constants import *

async def handle_qbwc(type: str, request: Request, data: dict):
    """Handle all QBWC SOAP requests"""
    try:
        # Get the raw XML body
        # raw_body = await request.body()
        # xml_string = raw_body.decode('utf-8')
        # method_name, params = parse_soap_request(xml_string)

        method_name = data.get("method")
        params = data.get("params", {})
        
        if not method_name:
            raise HTTPException(status_code=400, detail="Invalid SOAP request")
        
        sync_queue = await generate_sync_data(type)
        
        # Route to the appropriate handler
        if method_name == "authenticate":
            response_body = await handle_authenticate(sync_queue, params)
        elif method_name == "sendRequestXML":
            response_body = await handle_sendRequestXML(params)
        elif method_name == "receiveResponseXML":
            response_body = await handle_receiveResponseXML(params)
        elif method_name == "closeConnection":
            response_body = await handle_closeConnection(params)
        elif method_name == "serverVersion":
            response_body = await handle_serverVersion()
        elif method_name == "clientVersion":
            response_body = await handle_clientVersion(params)
        elif method_name == "connectionError":
            response_body = await handle_connectionError(params)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown SOAP method: {method_name}")

        return Response(
            content=response_body,
            media_type="text/xml; charset=utf-8"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling QBWC request: {e}")


async def generate_sync_data(type: str):
    """Generate data to be synced to QuickBooks"""
    try:
        # For demonstration, we will just return the constant data
        sync_queue = []
        data_to_sync = {
            "customers": CUSTOMERS_TO_SYNC,
            "employees": EMPLOYEES_TO_SYNC,
            "invoices": INVOICES_TO_SYNC,
            "gl_entries": GL_ENTRIES_TO_SYNC
        }
        
        for data in data_to_sync[type]:
            sync_queue.append({"type": type, "id": data['id'], "data": data})
        return sync_queue
    except Exception as e:
        raise Exception(f"Error generating data for sync: {e}")
