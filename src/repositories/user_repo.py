from src.core.config import settings
from src.schemas.user_schema import IAuth

class AuthenticateRepository:
    
    async def generate_send_otp(uid: str):
        _otp = otpgen()
        
        OTP_data = ( await db.session.execute(select(OtpModel).filter_by(uid = uid)) ).fetchone()
        if OTP_data is None:
            otp_info = OtpModel(
                uid = uid,
                otp = _otp
            )
            db.session.add(otp_info)
        else:
            OTP_data = OTP_data[0]
            OTP_data.otp = _otp
            db.session.add(OTP_data)       

        await db.session.commit()     
        return _otp
        
    async def login(login_data: IAuth, background_tasks):
        try:
            data = login_data.dict()
            async with db():  
                result = await db.session.execute( 
                    select(AuthModel).filter_by(email=data['email'])
                )
                auth_data = result.scalars().first()

                if auth_data is None:
                    return JSONResponse(status_code=404, content={"error": "User not found"})

                if not auth_data.isVerified:
                    _otp = await Authenticate.generate_send_otp(auth_data.uid)
                    email_content = {
                        "email": data['email'],
                        "subject": "Verify your account!",
                        "sender": f"{settings.app_name} Notifications",
                        "message": f"Hello New User,<br />We are happy to have you on board at {settings.app_name} Listings services.<br />Please use the code below to verify your account:<br/><b>{_otp}</b>"
                    }
                    return JSONResponse(status_code=400, content={"error": "User account is not verified"})

                # Log login attempt
                login_attempt_email_content = {
                    "email": data['email'],
                    "subject": "Login attempt",
                    "sender": f"{settings.app_name} Notifications",
                    "message": f"A login attempt was made on {settings.app_name} Listings services account using your email.<br />If this wasn't you, please contact us."
                }

                resp = generatejwt({
                    "auth_type": auth_data.auth_type,
                    "uid": auth_data.uid,
                    "email": auth_data.email,
                    "isVerified": auth_data.isVerified
                })
                return resp

        except Exception as ex:
            return JSONResponse(status_code=500, content={"error": str(ex)})
            
    async def remove(uid: str, user_id: str = None):
        try:
            await Accounts.delete_accounts(uid)
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
