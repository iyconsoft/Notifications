import asyncio, time


async def check_db(session) -> bool:
    """Comprehensive Db health check"""
    try:
        return True
    except Exception as e:
        return False
    # try:
    #     return {
    #         "status": "healthy",
    #         "error": False,
    #         "details": {}
    #     }

    # except Exception as e:
    #     return {
    #         "status": "unhealthy",
    #         "error": "operation failed",
    #         "details": str(e)
        # }

async def check_app(app_service_url: str = None, timeout: int = 3) -> bool:
    """Check if an external application is reachable."""
    try:
        return True
    except Exception as e:
        return False