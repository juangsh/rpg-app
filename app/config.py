import os
from dotenv import load_dotenv

load_dotenv()

APP_SECRET = os.getenv("APP_SECRET", "change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rpg.db")
