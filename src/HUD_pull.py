"""Reusable HUD Fair Market Rent pull (FERC-10)."""
import json
from pathlib import Path

import pandas as pd
import requests

from config import HUD_API_TOKEN, RAW_DIR

HUD_BASE_URL = "https://www.huduser.gov/hudapi/public/fmr"
STATE_CODE = "WI"

# HUD bedroom field -> our column name
BEDROOM_FIELDS = {
    "Efficiency":    "fmr_0br",
    "One-Bedroom":   "fmr_1br",
    "Two-Bedroom":   "fmr_2br",
    "Three-Bedroom": "fmr_3br",
    "Four-Bedroom":  "fmr_4br",
}
FMR_COLS = list(BEDROOM_FIELDS.values())


def pull_fmr_state(state_code=STATE_CODE, year=None):
    """Pull FMRs for every county and metro area in a state in one call.
    year=None asks HUD for its latest year; the year HUD actually
    returned is stored in the result"""
    url = f"{HUD_BASE_URL}/statedata/{state_code}"
    headers = {"Authorization": f"Bearer {HUD_API_TOKEN}",
               "Accept": "application/json"}
    params = {"year": year} if year else None

    resp = requests.get(url, headers=headers, params=params, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(f"HUD error {resp.status_code}: {resp.text[:200]}")
    try:
        return resp.json()
    except ValueError:
        raise RuntimeError(f"HUD sent non-JSON (bad token?): {resp.text[:200]}")


def save_raw(payload, state_code=STATE_CODE):
    """Save the untouched response to data/raw/ and return the path."""
    year = payload.get("data", {}).get("year", "unknown")
    path = Path(RAW_DIR) / f"hud_fmr_{year}_{state_code}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return path


def clean_fmr(payload):
    """Turn the response into two DataFrames: counties and metro areas.
    Bedroom rents become numbers; the HUD year is added to every row."""
    data = payload["data"]
    year = data["year"]

    counties = pd.DataFrame(data["counties"])
    metros = pd.DataFrame(data["metroareas"])

    for df in (counties, metros):
        df.rename(columns=BEDROOM_FIELDS, inplace=True)
        for c in FMR_COLS:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df["year"] = int(year)

    # First 5 digits of HUD's 10-digit fips_code = state + county FIPS,
    # which matches Census state + county. Use it to join the two sources.
    counties["fips_code"] = counties["fips_code"].astype(str)
    counties["county_fips5"] = counties["fips_code"].str[:5]
    return counties, metros



def pull_fmr(state_code=STATE_CODE, year=None):
    """Pull, save raw, clean, check. Returns (counties_df, metros_df)."""
    payload = pull_fmr_state(state_code, year)
    print(f"Saved raw -> {save_raw(payload, state_code)}")
    counties, metros = clean_fmr(payload)
    return counties, metros


if __name__ == "__main__":
    counties, metros = pull_fmr()
    print(counties.head())
    print(metros.head())