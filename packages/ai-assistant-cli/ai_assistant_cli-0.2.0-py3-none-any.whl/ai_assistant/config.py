import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

DATA_DIR = Path.home() / ".ai_assistant"
DATA_DIR.mkdir(exist_ok=True)
