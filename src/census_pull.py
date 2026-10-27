"""Reusable Census ACS 5-year pull (FERC-6)."""
import re
from pathlib import Path

import pandas as pd
import requests

from config import ACS_YEAR, CENSUS_API_KEY, RAW_DIR, STATE_FIPS

CORE_TABLES = [
    "B19001",   # household income (ALICE count)
    "B19037",   # income by age of householder (age-split demand)
    "B25063",   # gross rent distribution
    "B25087",   # mortgage status by monthly owner cost bracket
    "B25088",   # median monthly owner costs by mortgage status
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
MISSING_CODES = [-666666666, -999999999, -888888888,
                 -222222222, -333333333, -555555555]

# Matches estimate (E) and margin-of-error (M) columns, e.g. B19001_001E
EST_MOE_PATTERN = re.compile(r"^\w+_\d{3}[EM]$")

#modify to check for geo_code not tract
def _geo_params(geography, state, county="*"):
    """Build the 'for' and 'in' parts of the Census request."""
    if geography == "county":
        return [("for", "county:*"),
                ("in", f"state:{state}")]
    if geography == "tract":
        return [("for", "tract:*"),
                ("in", f"state:{state}"),
                ("in", f"county:{county}")]
    raise ValueError(f"geography must be 'county' or 'tract', got {geography!r}")


def pull_acs_table(table, year=ACS_YEAR, state=STATE_FIPS,
                   geography="county", county="*"):
    """Pull one whole ACS table (estimates + margins of error).
    geography='county': every county in the state.
    geography='tract':  every tract in the state, or in one county if
                        county is a 3-digit FIPS like '105'.
    Returns the data exactly as Census sent it (text)."""
    params = [("get", f"NAME,group({table})"),
              ("key", CENSUS_API_KEY)]
    params += _geo_params(geography, state, county)

    resp = requests.get(BASE_URL.format(year=year), params=params, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"Census error {resp.status_code} for {table}: {resp.text[:200]}")
    try:
        rows = resp.json()
    except ValueError:
        raise RuntimeError(f"Census sent non-JSON for {table} (bad key?): {resp.text[:200]}")
    return pd.DataFrame(rows[1:], columns=rows[0])


def save_raw(df, table, year=ACS_YEAR, geography="county"):
    """Save the untouched pull to data/raw/ and return the path.
     so a tract pull never overwrites a county pull."""
    path = Path(RAW_DIR) / f"acs5_{year}_{table}_{geography}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def clean_acs_table(df):
    """Keep id columns + estimate (E) and margin-of-error (M) columns;
    make them numeric; turn Census missing codes into NaN."""
    id_cols = [c for c in ["GEO_ID", "NAME", "state", "county", "tract"]
               if c in df.columns]
    est_moe = [c for c in df.columns if EST_MOE_PATTERN.match(c)]
    out = df[id_cols + est_moe].copy()
    for c in est_moe:
        out[c] = (pd.to_numeric(out[c], errors="coerce")
                  .replace(MISSING_CODES, float("nan")))
    return out


def pull_tables(tables, year=ACS_YEAR, state=STATE_FIPS,
                geography="county", county="*"):
    """Pull several tables, saving each raw. Returns {table: raw DataFrame}."""
    results = {}
    for t in tables:
        df = pull_acs_table(t, year, state, geography, county)
        path = save_raw(df, t, year, geography)
        print(f"{t}: {len(df)} rows, {df.shape[1]} columns -> {path}")
        results[t] = df
    return results


if __name__ == "__main__":
    ALL_TABLES = CORE_TABLES + QUALITY_SIZE_TABLES
    for geo in ["county", "tract"]:
        for t in ALL_TABLES:
            try:
                pull_tables([t], geo)
            except RuntimeError:
                print(f"failed for {t}: {geo}")