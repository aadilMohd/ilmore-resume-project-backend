from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException , APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime
import json
import time
import hashlib
from fastapi.responses import StreamingResponse

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

from app.ai.gemini import analyze_gemini_stream
from app.cache.redis_client import redis_client

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
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


# @app.post("/api/v1/analyze")
# async def analyze_resume(
#     resume_file: UploadFile = File(...),
#     jd_text: str = Form(...),
#     mode: str = Form("gemini"),
#     user_id: str = Depends(get_current_user),  # <-- 1. Require a valid VIP wristband!
#     db: AsyncSession = Depends(get_db)         # <-- 2. Open a database connection
# ):
    
#     # --- 1. QUOTA CHECK: Prevent going over 2 scans per month ---
#     now = datetime.utcnow()
#     start_of_month = datetime(now.year, now.month, 1)

#     quota_query = await db.execute(
#         select(func.count())
#         .select_from(Scan)
#         .where(Scan.user_id == user_id)
#         .where(Scan.created_at >= start_of_month)
#     )
#     monthly_scans_used = quota_query.scalar() or 0
    
#     user_email = await db.execute(select(User.email).where(User.id == user_id))

   
#     if monthly_scans_used >= 2 and user_email.scalar() != "mohd.aadil2602@gmail.com":
#         raise HTTPException(
#             status_code=403, 
#             detail="PAYWALL_TRIGGER"
#         )
#     # -------------------------------------------------------------

#     # 1. Read the uploaded PDF file into memory
#     file_bytes = await resume_file.read()
    
#     # 2. Extract the clean text
#     resume_text = extract_text_from_pdf(file_bytes)
    
#     # 3. If the PDF was unreadable, stop here
#     if not resume_text:
#         return {"error": "Could not extract text from the provided PDF."}
        
#     # 4. Fire the request to Gemini!
#     result = await route_and_analyze(
#         resume_text=resume_text, 
#         jd_text=jd_text, 
#         mode=mode
#     )
    
#     gemini_data = result.get("gemini_result")
#     match_score = gemini_data.get("match_score") if isinstance(gemini_data, dict) else None
    
#     # 5. Save the Scan to the Database
#     new_scan = Scan(
#         user_id=user_id,
#         jd_text=jd_text,
#         gemini_result=gemini_data,
#         match_score_gemini=match_score,
#         processing_time_ms=result.get("processing_time_ms")
#     )
    
#     db.add(new_scan)
#     await db.commit()
#     await db.refresh(new_scan)

#     result["scan_id"] = str(new_scan.id)
    
#     # 6. Update the user's total scan count
#     await db.execute(
#         update(User)
#         .where(User.id == user_id)  
#         .values(scan_count=User.scan_count + 1)
#     )
#     await db.commit()

#     # 7. Return the scan result to React
#     return result
 

@app.post("/api/v1/analyze")
async def analyze_resume(
    resume_file: UploadFile = File(...),
    jd_text: str = Form(...),
    mode: str = Form("gemini"),
    user_id: str = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)         
):
    
    # --- 1. QUOTA CHECK ---
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)

    quota_query = await db.execute(
        select(func.count())
        .select_from(Scan)
        .where(Scan.user_id == user_id)
        .where(Scan.created_at >= start_of_month)
    )
    monthly_scans_used = quota_query.scalar() or 0
    
    user_email_result = await db.execute(select(User.email).where(User.id == user_id))
    user_email = user_email_result.scalar()

    if monthly_scans_used >= 2 and user_email != "mohd.aadil2602@gmail.com":
        raise HTTPException(status_code=403, detail="PAYWALL_TRIGGER")

    # --- 2. EXTRACT PDF TEXT ---
    file_bytes = await resume_file.read()
    resume_text = extract_text_from_pdf(file_bytes)
    
    if not resume_text:
        return {"error": "Could not extract text from the provided PDF."}

    # --- 3. REDIS CACHE FINGERPRINT ---
    cache_key = hashlib.sha256(f"{resume_text}{jd_text}".encode()).hexdigest()
    redis_key = f"scan:{cache_key}"

    # --- 4. THE SSE STREAMING GENERATOR ---
    async def stream_and_save():
        start_time = time.time()
        
        # A. Check Redis for a Cache Hit
        cached_result = await redis_client.get(redis_key)
        if cached_result:
            print("CACHE HIT! Streaming pre-saved results.")
            try:
                cached_data = json.loads(cached_result)
                # Extract the saved AI result structure cleanly
                gemini_data = cached_data.get("gemini_result", {})
                
                # Turn the full object back into a string and send it in one clean SSE frame
                stringified_json = json.dumps(gemini_data)
                safe_payload = json.dumps({"token": stringified_json})
                
                yield f"data: {safe_payload}\n\n"
                yield f"event: done\ndata: {{}}\n\n"
                return # Exit early, we are done!
            except Exception as cache_err:
                print(f"Error parsing cache, falling back to live stream: {cache_err}")

        # B. Cache Miss: Stream live text from Gemini
        print("CACHE MISS. Connecting to Gemini...")
        full_json_result = ""
        
        try:
            async for chunk in analyze_gemini_stream(resume_text=resume_text, jd_text=jd_text):
                full_json_result += chunk  # Accumulate chunks for Redis and Database saves
                
                safe_payload = json.dumps({"token": chunk})
                yield f"data: {safe_payload}\n\n"
                
        except Exception as e:
            error_payload = json.dumps({"detail": str(e)})
            yield f"event: error\ndata: {error_payload}\n\n"
            return 

        # C. Processing Completed: Parse compiled output safely
        processing_time_ms = int((time.time() - start_time) * 1000)
        try:
            gemini_data = json.loads(full_json_result)
            match_score = gemini_data.get("match_score") if isinstance(gemini_data, dict) else None
        except json.JSONDecodeError:
            gemini_data = {"raw_output": full_json_result}
            match_score = None

        # D. Save to PostgreSQL Database
        try:
            new_scan = Scan(
                user_id=user_id,
                jd_text=jd_text,
                gemini_result=gemini_data, 
                match_score_gemini=match_score,
                processing_time_ms=processing_time_ms
            )
            db.add(new_scan)
            
            await db.execute(
                update(User)
                .where(User.id == user_id)  
                .values(scan_count=User.scan_count + 1)
            )
            await db.commit()
        except Exception as db_err:
            print(f"Database save error: {db_err}")

        # E. Save compiled object to Redis Cache (24 hours TTL)
        try:
            cache_payload = {
                "gemini_result": gemini_data,
                "mode": mode,
                "processing_time_ms": processing_time_ms
            }
            await redis_client.setex(redis_key, 86400, json.dumps(cache_payload))
            print("CACHE PACKED. Saved result to Redis.")
        except Exception as redis_err:
            print(f"Redis cache save error: {redis_err}")

        # F. Notify frontend of stream completion
        yield f"event: done\ndata: {{}}\n\n"

    # --- 5. EXECUTE STREAM RESPONSE ---
    return StreamingResponse(
        stream_and_save(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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