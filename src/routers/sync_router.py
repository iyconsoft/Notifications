from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils import build_success_response, build_error_response
from src.core.config import logging, settings
from src.repositories import handle_qbwc

syncRouter = APIRouter()

async def get_remote_db(request: Request):
    async with request.app.state.remotedbsession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

@syncRouter.post("", summary="Sync all modules endpoint")
async def sync_customers(request: Request, data: dict, remotedb: AsyncSession = Depends(get_remote_db) ):
    """Endpoint to handle QuickBooks Web Connector sync requests"""
    try:
        return await handle_qbwc(remotedb, None, request, data)
    except Exception as e:
        return build_error_response(
            f"Error processing sync type: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )

@syncRouter.post("/{type}", summary="Sync Endpoint")
async def sync_customers(type: str, request: Request, data: dict, remotedb: AsyncSession = Depends(get_remote_db)):
    """Endpoint to handle QuickBooks Web Connector sync requests"""
    try:
        if type not in settings.qwbcmodules:
            return build_error_response(
                f"Invalid sync type: {type}", status.HTTP_400_BAD_REQUEST, {}
            )

        return await handle_qbwc(remotedb, type, request, data)
    except Exception as e:
        return build_error_response(
            f"Error processing sync type: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )
