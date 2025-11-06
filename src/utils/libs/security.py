import os, base64, hashlib, binascii
from random import Random
import random as r

from fastapi.responses import JSONResponse

def generate_random_number(min_value, max_value):
    random_byte = os.urandom(1)  # Generate a random byte
    random_int = int.from_bytes(random_byte, byteorder="big")  # Convert byte to integer
    return min_value + random_int % (max_value - min_value + 1)


def otpgen():
    otp = ""
    for i in range(6):
        otp += str(generate_random_number(1,9))
    return otp

blocked_ips = set()
async def block_ips(request, call_next):
    forwarded_for = request.headers.get('X-Forwarded-For')
    ip = forwarded_for.split(",")[0] if forwarded_for else request.client.host
    # from core.dbconfig import db
    # from sqlalchemy import select

    # async with db():
    #     data = (await db.session.execute(select(AccountsModel).filter_by(uid = userinfo['uid']))).scalar_one_or_none()
    #     if data is None:
    #         raise HTTPException(status_code = 403, detail="user not found, access forbidden")
        
    if ip in blocked_ips:
        return JSONResponse(content={"detail": "Your IP is blocked"}, status_code=403)
    
    response = await call_next(request)
    return response


