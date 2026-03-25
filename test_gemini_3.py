import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content("Dis bonjour au monde agricole.")
    print("Response from Gemini:", response.text)
    print("SUCCESS")
except Exception as e:
    print("FAILED:", str(e))
