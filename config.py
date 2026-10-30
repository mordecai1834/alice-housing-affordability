import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
HUD_API_TOKEN = os.getenv("HUD_API_TOKEN")

DB_PATH = BASE_DIR / "db" / "alice.db"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

# Locked vintages (Field Guide Step 1)
ACS_YEAR = 2024
STATE_FIPS = "55"