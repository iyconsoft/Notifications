from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import Response
from src.utils import build_success_response, build_error_response
from src.core.config import logging, settings
from src.repositories import handle_qbwc

syncRouter = APIRouter()

@syncRouter.post("", summary="Sync all modules endpoint")
async def sync_customers(request: Request, data: dict):
    """Endpoint to handle QuickBooks Web Connector sync requests"""
    try:
        for module in settings.qwbcmodules:
            return await handle_qbwc(module, request, data)
    except Exception as e:
        return build_error_response(
            f"Error processing sync type: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )

@syncRouter.post("/{type}", summary="Sync Endpoint")
async def sync_customers(type:str, request: Request, data: dict):
    """Endpoint to handle QuickBooks Web Connector sync requests"""
    try:
        if type not in settings.qwbcmodules:
            return build_error_response(
                f"Invalid sync type: {type}", status.HTTP_400_BAD_REQUEST, {}
            )

        return await handle_qbwc(type, request, data)
    except Exception as e:
        return build_error_response(
            f"Error processing sync type: {e}", status.HTTP_500_INTERNAL_SERVER_ERROR, {}
        )
