import jwt
from datetime import datetime, timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

# This tells FastAPI to look for a "Bearer Token" in the header of incoming requests
security = HTTPBearer()

def verify_google_token(token: str) -> dict:
    """
    Takes the token the frontend got from Google, and asks Google's servers:
    'Hey, is this a real token, and was it issued for my Campus Copilot app?'
    """
    try:
        idinfo = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        return idinfo # Returns a dictionary with their email, name, picture, etc.
    except ValueError:
        # If the token is fake, expired, or belongs to another app, reject it!
        raise HTTPException(status_code=401, detail="Invalid Google auth token")

def create_jwt_token(user_id: str) -> str:
    """
    Once we trust the user, we print them a VIP wristband (JWT) valid for 7 days.
    They will use this for all future API calls so they don't have to keep logging in.
    """
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {
        "sub": str(user_id), # We store their database ID inside the token
        "exp": expire
    }
    # Cryptographically sign it using your secret key from the .env file
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    We will attach this to our protected endpoints. It intercepts the request, 
    checks the wristband, and returns the user's ID if the wristband is valid.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Your VIP wristband has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid VIP wristband.")