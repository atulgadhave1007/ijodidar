import os
from dotenv import load_dotenv

# ✅ Load .env before importing app
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from app import app  # Import after env is loaded

if __name__ == "__main__":
    app.run()