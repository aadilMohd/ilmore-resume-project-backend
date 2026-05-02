import json
import anthropic
from app.config import settings

# 1. The System Prompt sets the Career Coach persona
SYSTEM_PROMPT = """
You are an expert career coach specializing in Indian job markets and campus placements.
You have deep knowledge of what makes resumes stand out for Indian tech companies, 
consulting firms, and startups. You write in clear, direct language suited for 
college students and early-career professionals.

You always respond ONLY with valid JSON. No preamble, no explanation, no markdown fences.
"""

# 2. The User Prompt formats the exact JSON response we need
USER_PROMPT = """
ADDITIONAL CONTEXT:
{context}

RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Provide resume analysis in this exact JSON format:
{{
  "match_score": 80,
  "score_reason": "<concise one-line explanation>",
  "missing_keywords": ["keyword1", "keyword2"],
  "strong_points": ["point1", "point2"],
  "suggestions": [
    {{
      "original": "<current bullet point>",
      "improved": "<stronger, quantified version>"
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
"""

async def analyze_claude(resume_text: str, jd_text: str, context: str = "") -> dict:
    """
    Sends the resume and JD to Claude Sonnet and returns a structured JSON dictionary.
    """
    # Initialize the async Anthropic client
    client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    
    prompt = USER_PROMPT.format(
        context=context,
        resume_text=resume_text[:3000], # Safety truncation
        jd_text=jd_text[:2000]
    )
    
    try:
        # Fire the request to Anthropic's servers
        # Using the standard Sonnet 3.5 model which is incredibly fast and smart
        response = await client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=2000,
            temperature=0.3, # Keep it analytical
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Claude returns a list of text blocks, we want the text from the first one
        response_text = response.content[0].text
        
        # Strip any markdown fences just in case Claude gets chatty
        clean_text = response_text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(clean_text)
        
    except Exception as e:
        print(f"Failed to parse Claude JSON: {e}")
        return {"error": str(e)}