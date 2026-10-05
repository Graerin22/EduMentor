import os
from pathlib import Path
from dotenv import load_dotenv, set_key

ROOT_DIR = Path(__file__).resolve().parents[1]
env_file = ROOT_DIR / '.env'

if not env_file.exists():
    env_file.write_text("GEMINI_API_KEY=\nGEMINI_MODEL=")

load_dotenv()

def set_api_key(key):
    set_key(env_file, 'GEMINI_API_KEY', key)
    load_dotenv(override=True)

def set_model(model):
    set_key(env_file, 'GEMINI_MODEL', model)
    load_dotenv(override=True)

def get_model():
    return os.getenv('GEMINI_MODEL')