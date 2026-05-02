from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime

# --- Our App Imports ---
from app.utils.pdf_parser import extract_text_from_pdf
from app.ai.router import route_and_analyze
from app.routers import auth
from app.utils.auth import get_current_user  # <-- The Bodyguard
from app.database import get_db              # <-- The Database connection
from app.models.scan import Scan             # <-- The Scan table
from app.models.user import User 

# --- App Initialization ---
app = FastAPI(title="Campus Copilot API", version="1.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "theilmora.com",
        "https://theilmora.com",
        "https://www.theilmora.com",
        "https://ilmora-resume-project-frontend.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(auth.router, tags=["Authentication"])

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Campus Copilot API is running"}


@app.post("/api/v1/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
    mode: str = Form("gemini"),
    user_id: str = Depends(get_current_user),  # <-- 1. Require a valid VIP wristband!
    db: AsyncSession = Depends(get_db)         # <-- 2. Open a database connection
):
    
    # --- 1. QUOTA CHECK: Prevent going over 2 scans per month ---
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    quota_query = await db.execute(
        select(func.count())
        .select_from(Scan)
        .where(Scan.user_id == user_id)
        .where(Scan.created_at >= start_of_month)
    )
    monthly_scans_used = quota_query.scalar() or 0
    
    user_email = await db.execute(select(User.email).where(User.id == user_id))

   
    if monthly_scans_used >= 2 and user_email.scalar() != "mohd.aadil2602@gmail.com":
        raise HTTPException(
            status_code=403, 
            detail="PAYWALL_TRIGGER"
        )
    # -------------------------------------------------------------

    # 1. Read the uploaded PDF file into memory
    file_bytes = await resume_file.read()
    
    # 2. Extract the clean text
    resume_text = extract_text_from_pdf(file_bytes)
    
    # 3. If the PDF was unreadable, stop here
    if not resume_text:
        return {"error": "Could not extract text from the provided PDF."}
        
    # 4. Fire the request to Gemini!
    result = await route_and_analyze(
        resume_text=resume_text, 
        jd_text=jd_text, 
        mode=mode
    )
    
    gemini_data = result.get("gemini_result")
    match_score = gemini_data.get("match_score") if isinstance(gemini_data, dict) else None
    
    # 5. Save the Scan to the Database
    new_scan = Scan(
        user_id=user_id,
        jd_text=jd_text,
        gemini_result=gemini_data,
        match_score_gemini=match_score,
        processing_time_ms=result.get("processing_time_ms")
    )
    
    db.add(new_scan)
    await db.commit()
    await db.refresh(new_scan)

    result["scan_id"] = str(new_scan.id)
    
    # 6. Update the user's total scan count
    await db.execute(
        update(User)
        .where(User.id == user_id)  
        .values(scan_count=User.scan_count + 1)
    )
    await db.commit()

    # 7. Return the scan result to React
    return result
 

@app.get("/api/v1/scans")
async def get_user_scans(
    user_id: str = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)         
):
    """
    Fetches the entire scan history for the logged-in user, newest first.
    """
    query = select(Scan).where(Scan.user_id == user_id).order_by(Scan.created_at.desc())
    result = await db.execute(query)
    user_scans = result.scalars().all()
    
    return {"scans": user_scans}