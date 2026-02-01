from fastapi.responses import JSONResponse

def build_success_response(message: str, status: int = 200, data = None):
    resp = {
        "success": True,
        "message": message,
    }
    if data is not None:
        resp['data'] = data
    return JSONResponse(
        status_code=status,
        content=resp
    )


def build_error_response(message: str, status: int = 400, data: dict = None):
    resp = {
        "success": True,
        "error_message": message,
    }
    if data is not None:
        resp['data'] = data
    return JSONResponse(
        status_code=status,
        content=resp
    )

