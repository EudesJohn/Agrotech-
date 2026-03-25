import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("Listing available models:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
