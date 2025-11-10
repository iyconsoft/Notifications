from src.services import *
from src.constants import *
from src.core import settings, db
from sqlalchemy import text

async def handle_qbwc(dbsession, type: str, request: Request, data: dict):
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
        
        sync_queue = await generate_sync_data(dbsession, type)
        
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


async def generate_sync_data(session, type: str):
    """Generate data to be synced to QuickBooks"""
    try:
        sync_queue = []
        # if settings.is_demo is False:
        #     CUSTOMERS_TO_SYNC = await get_remote_data(session, "customers")
        #     EMPLOYEES_TO_SYNC = await get_remote_data(session, "employees")
        #     INVOICES_TO_SYNC = await get_remote_data(session, "invoices")
        #     GL_ENTRIES_TO_SYNC = await get_remote_data(session, "gl_entries")

        data_to_sync = {
            "customers": CUSTOMERS_TO_SYNC,
            "employees": EMPLOYEES_TO_SYNC,
            "invoices": INVOICES_TO_SYNC,
            "gl_entries": GL_ENTRIES_TO_SYNC
        }

        if type is None:            
            for module in settings.qwbcmodules:
                for data in data_to_sync[module]:
                    sync_queue.append({"type": module, "id": data['id'], "data": data, "retries": 0})
        else:
            for data in data_to_sync[type]:
                sync_queue.append({"type": type, "id": data['id'], "data": data, "retries": 0})

        logging.info(f"sync data {sync_queue}")
        return sync_queue
    except Exception as e:
        raise Exception(f"Error generating data for sync: {e}")


async def get_remote_data(session, table: str, limit: int = 100):
    """Get data to be synced to QuickBooks from remote db"""
    try:
        stmt = text(f"SELECT * FROM {table} LIMIT :limit")
        result = await session.execute(stmt, {"limit": limit})
        rows = result.fetchall()
    except Exception as e:
        raise Exception(f"Error generating data for sync: {e}")
