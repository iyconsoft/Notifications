from fastapi.responses import JSONResponse
from sqlalchemy import select
from src.core import settings, db
from src.utils import build_success_response, build_error_response
from src.utils.libs import EmailLib, generatejwt
from src.schemas.user_schema import IAuth, IUser, User

class AuthenticateRepository:
    
    async def generate_send_otp(user: IAuth):
        _otp = otpgen()
        async with db():  
            user.otp = _otp
            db.session.add(OTP_data)  
            await db.session.commit()     
            return _otp
        
    async def login(login_data: IAuth, background_tasks):
        try:
            data = login_data.dict()
            async with db():  
                result = await db.session.execute( select(User).filter_by(email=data['email']) )
                auth_data = result.scalars().first()

                if auth_data is None:
                    return JSONResponse(status_code=404, content={"error": "User not found"})

                _otp = await AuthenticateRepository.generate_send_otp(auth_data)
                await EmailLib.send_email(
                    "Verify your account!", data['email'], 
                    f"Hello New User,<br />We are happy to have you on board at {settings.app_name}.<br />Please use the code below to verify your account:<br/><b>{_otp}</b>"
                )
                return build_success_response(message="email account otp sent")
        
        except Exception as ex:
            return JSONResponse(status_code = 500, content = { "error": str(ex) } )

    async def verify(data: IAuth, background_tasks):
        try:
            data = data.dict()
            async with db():  
                result = await db.session.execute( 
                    select(User).filter_by(email=data['uid'])
                )
                auth_data = result.scalars().first()

                if auth_data is None:
                    return JSONResponse(status_code=404, content={"error": "User not found"})

                return generatejwt({
                    "auth_type": auth_data.auth_type,
                    "uid": auth_data.uid,
                    "email": auth_data.email,
                    "isVerified": auth_data.isVerified
                })

        except Exception as ex:
            return JSONResponse(status_code=500, content={"error": str(ex)})
            
    async def remove(uid: str, user_id: str = None):
        try:
            await User.delete_accounts(uid)
            if uid == user_id :
                _revoke_tokens()

            return {
                "message": "account deleted"
            }
        except Exception as ex:
            return JSONResponse(status_code = 500, content = { "error": str(ex) } )

    async def logout():
        try:
            return {
                "message": _revoke_tokens()
            }
        except Exception as ex:
            return JSONResponse(status_code = 500, content = { "error": str(ex) } )



class UserRepository:
    
    async def create(user_data: IUser):
        try:
            data = user_data.dict()
            async with db():  
                result = await db.session.execute( select(User).filter_by(email=data['email']) )
                auth_data = result.scalars().first()

                if auth_data is not None:
                    return JSONResponse(status_code=404, content={"error": "User found"})
                
                _user = User(
                    email = data['email'],
                    uid = data['uid'],
                    otp = None,
                    firstname = data['firstname'],
                    lastname = data['lastname'],
                )
                db.session.add(_user)  
                await db.session.commit() 
                
                return build_success_response("user registered", 201)

        except Exception as ex:
            return JSONResponse(status_code = 500, content = { "error": str(ex) } )
 
    async def get_user(uid: str):
        try:
            async with db():  
                result = await db.session.execute( select(User).filter_by(uid = uid) )
                userdata = result.scalars().first()
                user = {} if userdata is None else {
                    "firstname": userdata.firstname,
                    "lastname": userdata.lastname,
                    "uid": userdata.uid,
                    "email": userdata.email,
                }
                return build_success_response("user retrieved successfully", 200, user)
                    
        except Exception as ex:
            return build_error_response(str(ex), 500 )

