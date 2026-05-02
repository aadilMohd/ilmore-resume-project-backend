from google import genai
from app.config import settings

print("Connecting to Google AI Studio with the new SDK...")

try:
    # Initialize the modern client
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    print("\nYour API key has access to these models:")
    
    # Fetch the list of authorized models
    for model in client.models.list():
        # We only want models that can generate content
        if 'generateContent' in model.supported_generation_methods:
            print(f" - {model.name}")
            
except Exception as e:
    print(f"\nError fetching models: {e}")