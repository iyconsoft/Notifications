
from fastapi import HTTPException
import os, jwt
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def validate_token(token: str):
    try:  
        userinfo = jwt.decode(token, os.getenv("SECRET_KEY"), [os.getenv("JWT_ACCESS_ALGORITHM")])
        return userinfo
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="JWT has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid JWT",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(status_code = 403, detail=str(e) if str(e) != '' else "access forbidden and denied")


def generatejwt(user: dict):
    try:  
        expire = datetime.utcnow() + timedelta(days=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE")))
        to_encode = user.copy()
        to_encode.update({"exp": expire})
        return { 
            "access_token": jwt.encode(
                to_encode,
                os.getenv("SECRET_KEY"),
            ),
            "refresh_token": jwt.encode(
                to_encode,
                os.getenv("SECRET_KEY"),
            )
        }
    except Exception as e:
        raise Exception(str(e))

