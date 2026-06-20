from datetime import datetime
import json
from google import genai
from google.genai import types
from app.config import settings

# 1. The System Prompt sets the persona
SYSTEM_PROMPT = """
You are a senior technical recruiter with 15+ years of experience in software engineering hiring.
Your task is to evaluate a candidate's resume against a Job Description with surgical precision.

---
## STEP 1 — INTERNAL ANALYSIS (do this silently, do not output it)

Before writing JSON, reason through the following in your head:
1. List every required skill in the JD. Mark each as: EXACT MATCH / PARTIAL / MISSING.
2. Calculate years of relevant experience vs. JD requirement.
3. Identify quantified achievements (numbers, percentages, scale metrics).
4. Note role title and industry alignment.

---
## STEP 2 — SCORING RUBRIC (deterministic, apply exactly)

Start at 0. Add points using ONLY these rules:

### Experience Match (max 30 pts)
| Condition                                      | Points |
|------------------------------------------------|--------|
| Years of experience meets or exceeds JD        | +15    |
| Domain/industry is an exact match              | +10    |
| Role title is the same or one level off        | +5     |

### Skill Match (max 50 pts)
| Condition                                      | Points |
|-------------------------------------------|--------|
| Each EXACT skill match from JD (max 10)   | +5 each|
| Each PARTIAL skill match                  | +2 each|
| Missing required skill                    | +0     |

### Impact & Metrics (max 20 pts)
| Condition                                      | Points |
|------------------------------------------------|--------|
| 3+ bullet points have hard numbers/metrics     | +20    |
| 1–2 bullet points have metrics                 | +10    |
| No measurable impact anywhere                  | +0     |

Cap final score at 100.

---
## STEP 3 — OUTPUT RULES

- Output ONLY a single valid JSON object. No markdown. No explanation. No preamble. No trailing text.
- Do NOT hallucinate skills, metrics, or experience not in the resume.
- `match_score`: integer 0–100.
- `score_reason`: 2–3 sentences explaining EXACTLY which rubric lines were triggered and why.
- `strong_points`: exactly 3 strings. Each must reference a specific skill or experience from the resume.
- `missing_keywords`: exactly 3–5 strings. Each is a skill/tool/keyword in the JD not found in the resume.
- `suggestions`: exactly 3 objects. Each must rewrite a WEAK or VAGUE resume bullet into a STRONG one.
- `interview_questions`: exactly 4 strings. 2 must be technical deep-dives; 2 must be behavioral.

---
## FEW-SHOT EXAMPLES

### suggestions — Bad vs. Good
❌ Original: "Worked on the backend."
✅ Improved: "Architected 3 FastAPI microservices handling 50K daily requests, reducing average response time by 40% via async DB connection pooling."

### interview_questions — Bad vs. Good
❌ "Tell me about yourself."
✅ Technical: "You listed Redis — walk me through a caching scenario. What was your eviction strategy and why?"
✅ Behavioral: "Describe a time you pushed back on a product requirement. What was the outcome?"
"""
# 2. The User Prompt formats the request
USER_PROMPT = """
CONTEXT FROM OUR KNOWLEDGE BASE:
{context}

CANDIDATE RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Analyze this resume against the job description and respond with this exact JSON:
{{
  "match_score": 75,
  "score_reason": "<one sentence explaining the score>",
  "missing_keywords": ["keyword1", "keyword2", "keyword3"],
  "strong_points": ["strength1", "strength2"],
  "suggestions": [
    {{
      "original": "<exact bullet from resume that can be improved>",
      "improved": "<rewritten version with metrics, action verbs, impact>"
    }}
  ],
  "interview_questions": [
    "<question 1>",
    "<question 2>",
    "<question 3>",
    "<question 4>",
    "<question 5>"
  ]
}}

Rules:
- missing_keywords: list exactly what is in the JD but missing from resume (max 10)
- suggestions: rewrite 2-3 of the weakest bullets, add metrics where possible
- interview_questions: predict what the hiring manager will ask based on this specific JD
- Be specific to Indian hiring context (mention CGPA, projects, internships where relevant)
"""

async def analyze_gemini(resume_text: str, jd_text: str, context: str = "") -> dict:
    """
    Sends the resume and JD to Gemini using the new google-genai SDK.
    """
    # Initialize the modern client
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Inject the actual resume and JD text into the prompt template
    prompt = USER_PROMPT.format(
        context=context,
        resume_text=resume_text[:3000],  
        jd_text=jd_text[:2000]
    )
    
    try:
        # Fire the async request using the new client.aio architecture
        # We are using 1.5-flash as it is the most stable and fast model for this SDK
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                response_mime_type="application/json",
            )
        )
        
        return json.loads(response.text)
        
    except Exception as e:
        print(f"Failed to parse Gemini JSON: {e}")
        return {"error": str(e)}

async def analyze_gemini_stream(resume_text: str, jd_text: str, context: str = ""):
    """
    Connects asynchronously to Gemini and yields text chunks in real-time
    using the modern google-genai streaming SDK architecture.
    """
    # Initialize the modern client
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # Inject the text into your template
    prompt = USER_PROMPT.format(
        context=context,
        resume_text=resume_text[:3000],  
        jd_text=jd_text[:2000]
    )
    
    try:
        # 1. CHANGE HERE: Use generate_content_stream instead of generate_content
        response = await client.aio.models.generate_content_stream(
            model='gemini-3.1-flash-lite',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                # Note: Keeping response_mime_type guarantees Gemini outputs JSON characters,
                # which our frontend `jsonrepair` library parses on the fly!
                response_mime_type="application/json",
            )
        )
        
        # 2. CHANGE HERE: Loop over the async response stream and yield text chunks immediately
        async for chunk in response:
            if chunk.text:
                now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{now}] 🔥 CHUNK: {chunk.text!r}")
                
                yield chunk.text
                
    except Exception as e:
        print(f"Gemini Streaming Error: {e}")
        # Yield an explicit error string so the downstream handler catches it
        yield json.dumps({"error": f"Model stream execution failed: {str(e)}"})