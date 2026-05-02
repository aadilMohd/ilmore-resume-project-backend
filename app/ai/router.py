import json
import time
import hashlib
from app.ai.gemini import analyze_gemini
# from app.ai.claude import analyze_claude  # <-- Ready for when you drop the $5!
from app.cache.redis_client import redis_client

async def route_and_analyze(resume_text: str, jd_text: str, mode: str = "gemini") -> dict:
    # 1. Generate a unique fingerprint for this exact resume + JD combo
    cache_key = hashlib.sha256(f"{resume_text}{jd_text}".encode()).hexdigest()
    
    # 2. Check Redis!
    cached_result = await redis_client.get(f"scan:{cache_key}")
    if cached_result:
        print("CACHE HIT! Skipping AI APIs.")
        # We found it! Parse the JSON string back into a dictionary
        data = json.loads(cached_result)
        data["cached"] = True
        return data
        
    print("CACHE MISS. Sending to AI...")
    start_time = time.time()
    
    # 3. Dispatch to the correct AI engine
    result = {}
    if mode == "gemini":
        result["gemini"] = await analyze_gemini(resume_text, jd_text)
    
    # --- FUTURE CLAUDE LOGIC (Commented out for MVP) ---
    # elif mode == "claude":
    #     result["claude"] = await analyze_claude(resume_text, jd_text)
    # elif mode == "both":
    #     import asyncio
    #     gemini_res, claude_res = await asyncio.gather(
    #         analyze_gemini(resume_text, jd_text),
    #         analyze_claude(resume_text, jd_text),
    #         return_exceptions=True
    #     )
    #     result["gemini"] = gemini_res if not isinstance(gemini_res, Exception) else {"error": "Failed"}
    #     result["claude"] = claude_res if not isinstance(claude_res, Exception) else {"error": "Failed"}
    
    result["mode"] = mode
    result["processing_time_ms"] = int((time.time() - start_time) * 1000)
    result["cached"] = False
    
    # 4. Save the result to Redis so we never have to process this exact combo again!
    # 86400 seconds = 24 hours TTL (Time To Live)
    await redis_client.setex(
        f"scan:{cache_key}", 
        86400, 
        json.dumps(result)
    )
    
    return result