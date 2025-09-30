from fastapi.responses import JSONResponse

def build_success_response(message: str, status: int = 200, data: dict = None):
    return JSONResponse(
        status_code=status,
        content={
            "success": True,
            "message": message,
            "status_code": status,
            "data": data or {}
        }
    )


def build_error_response(message: str, status: int = 400, data: dict = None):
    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error_message": message,
            "status_code": status,
            "data": data or {}
        }
    )
