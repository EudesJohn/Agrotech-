import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

api_key = os.getenv('GEMINI_API_KEY')
print(f"Testing with API Key: {api_key[:10]}...")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Dis bonjour au monde agricole.")
    print("Response from Gemini:", response.text)
    print("SUCCESS")
except Exception as e:
    print("FAILED:", str(e))
