from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.utils.auth import verify_google_token, create_jwt_token

router = APIRouter()

# 1. Pydantic Schema to accept the token from the frontend
class GoogleLoginRequest(BaseModel):
    credential: str

@router.post("/api/v1/login")
async def login_with_google(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Receives the Google token, verifies it, updates the DB, and returns a JWT.
    """
    # 2. Hand the token to the Bouncer to verify with Google
    google_user = verify_google_token(request.credential)
    
    email = google_user.get("email")
    name = google_user.get("name")
    google_sub = google_user.get("sub")
    avatar_url = google_user.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Google token did not contain an email")

    # 3. Check if this user already exists in your Supabase database
    result = await db.execute(select(User).where(User.email == email))
    db_user = result.scalar_one_or_none()

    # 4. If they are a new user, create their account!
    if not db_user:
        db_user = User(
            email=email,
            name=name,
            google_sub=google_sub,
            avatar_url=avatar_url,
            plan="free",
            scan_count=0
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user) # Get their newly generated UUID

    # 5. Print the VIP wristband using their database ID
    access_token = create_jwt_token(db_user.id)

    # 6. Hand the wristband and user details back to the frontend
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(db_user.id),
            "email": db_user.email,
            "name": db_user.name,
            "avatar_url": db_user.avatar_url,
            "plan": db_user.plan
        }
    }