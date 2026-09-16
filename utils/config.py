import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    return os.getenv('GEMINI_API_KEY')

def get_model():
    return os.getenv('GEMINI_MODEL')