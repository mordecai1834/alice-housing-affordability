"""Reusable Census ACS 5-year pull (FERC-6)."""
from pathlib import Path

import pandas as pd
import requests

from config import ACS_YEAR, CENSUS_API_KEY, RAW_DIR, STATE_FIPS
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

BASE_URL = "https://api.census.gov/data/{year}/acs/acs5"
# Census "no data" codes that must never be treated as real numbers
MISSING_CODES = [-666666666, -999999999, -888888888, -222222222, -333333333, -555555555]

def GEO_PARAMS(geography, state, county):
    if geography == "count":
        return [("for", "county:*"), ("in", f"state:{state}")]
    if geography == "tract":
        return [("for","tract"),("for", "county:*"), ("in", f"state:{state}")]
    else:
        raise RuntimeError(f"Census error geography must include {state}, {county}, or {tract}")

def pull_acs_table(table, year=ACS_YEAR, state=STATE_FIPS):
    """Pull one whole ACS table (estimates + margins of error) for every
    county in a state. Returns the data exactly as Census sent it (text)."""
    params = {
        "get": f"NAME,group({table})",
        "for": "county:*",
        "in": f"state:{state}",
        "key": CENSUS_API_KEY,
    }
    resp = requests.get(BASE_URL.format(year=year), params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"Census error {resp.status_code} for {table}: {resp.text[:200]}")
    try:
        rows = resp.json()
    except ValueError:
        raise RuntimeError(f"Census sent non-JSON for {table} (bad key?): {resp.text[:200]}")
    return pd.DataFrame(rows[1:], columns=rows[0])


def save_raw(df, table, year=ACS_YEAR):
    """Save the untouched pull to data/raw/ and return the path."""
    path = Path(RAW_DIR) / f"acs5_{year}_{table}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def clean_acs_table(df):
    """Keep ids + estimate (E) and margin-of-error (M) columns; make them
    numeric; turn Census missing codes into NaN."""
    est_moe = [c for c in df.columns if c[-4:-1].isdigit() and c.endswith(("E", "M"))
               and c[-5] == "_"]
    out = df[["GEO_ID", "NAME", "state", "county"] + est_moe].copy()
    for c in est_moe:
        out[c] = pd.to_numeric(out[c], errors="coerce").replace(MISSING_CODES, float("nan"))
    return out


def pull_tables(tables, year=ACS_YEAR, state=STATE_FIPS):
    """Pull several tables, saving each raw. Returns {table: raw DataFrame}."""
    results = {}
    for t in tables:
        df = pull_acs_table(t, year, state)
        print(f"{t}: {len(df)} counties, {df.shape[1]} columns -> {save_raw(df, t, year)}")
        results[t] = df
    return results


if __name__ == "__main__":
    pull_tables(CORE_TABLES + QUALITY_SIZE_TABLES)