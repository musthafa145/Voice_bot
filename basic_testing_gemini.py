from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Test Gemini connection
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='Hello, are you working?'
)
print("Gemini Response:", response.text)
