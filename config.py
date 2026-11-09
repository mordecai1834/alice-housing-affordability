import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
HUD_API_TOKEN = os.getenv("HUD_API_TOKEN")

DB_PATH = BASE_DIR / "db" / "alice.db"
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "Processed_DIR"
EXCEL_EXPORT = BASE_DIR / "data" / "xlsx_exports"

CORE_TABLES = [
    "B19001",   # household income (ALICE count)
    "B19037",   # income by age of householder (age-split demand)
    "B25063",   # gross rent distribution
    "B25087",   # owner costs with mortgage
    "B25088",   # Monthly owner costs with mortgage
    "B25007",   # tenure by age
    "B25027",   # mortgage status by age
    "B25093",   # owner costs as % of income, by age
    "B25072",   # gross rent as % of income, by age
]
QUALITY_SIZE_TABLES = [
    "B25041",   # bedrooms (size)
    "B25034",   # year built (quality proxy)
    "B25047",   # plumbing (quality filter)
    "B25051",   # kitchen (quality filter)
    "B25014",   # overcrowding (quality filter)
]
HOUSE_HOLD_DESCRIPTIVE_VARIABLES = [
    "B11007",#Household with somone 65+
    "B09021",#Living arragnment(alone/ with spouse/ with others)
    "B12002",#Marital status by age, detail
]

CORE_QUALITY_TABLES = CORE_TABLES + QUALITY_SIZE_TABLES
ALL_TABLES = CORE_TABLES + QUALITY_SIZE_TABLES + HOUSE_HOLD_DESCRIPTIVE_VARIABLES
# Locked vintages (Field Guide Step 1)
ACS_YEAR = 2024
STATE_FIPS = "55"