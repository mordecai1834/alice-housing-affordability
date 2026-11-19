import json
from pathlib import Path

import pandas as pd
import requests

from config import RAW_DIR

LIHTC_URL = ("https://egis.hud.gov/arcgis/rest/services/gotit/"
             "LIHTCProperties/MapServer/0/query")
STATE_CODE = "WI"

ROCK_COUNTY_CITIES = [
    "JANESVILLE", "BELOIT", "EDGERTON", "EVANSVILLE", "MILTON",
    "CLINTON", "FOOTVILLE", "ORFORDVILLE",
]

# HUD field -> our column name
LIHTC_FIELDS = {
    "HUD_ID":    "hud_id",
    "PROJECT":   "project",
    "STD_ADDR":  "address",
    "STD_CITY":  "city",
    "STD_ST":    "state",
    "STD_ZIP5":  "zip5",
    "N_UNITS":   "total_units",
    "LI_UNITS":  "low_income_units",
    "METRO":     "metro_flag",
    "COMPANY":   "contact_company",
    "CONTACT":   "owner_contact",
    "CO_TEL":    "contact_phone",
}

UNIT_COLS = ["total_units", "low_income_units"]


def pull_lihtc(state_code=STATE_CODE, cities=ROCK_COUNTY_CITIES, page_size=1000):
    city_list = ",".join(f"'{c}'" for c in cities)
    where = f"STD_ST='{state_code}' AND UPPER(STD_CITY) IN ({city_list})"
    features, offset = [], 0

    while True:
        params = {
            "where": where,
            "outFields": ",".join(LIHTC_FIELDS),
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "json",
        }
        resp = requests.get(LIHTC_URL, params=params, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"HUD error {resp.status_code}: {resp.text[:200]}")
        try:
            payload = resp.json()
        except ValueError:
            raise RuntimeError(f"HUD sent non-JSON: {resp.text[:200]}")
        if "error" in payload:
            raise RuntimeError(f"HUD query error: {payload['error']}")

        batch = payload.get("features", [])
        features.extend(batch)
        if not payload.get("exceededTransferLimit") or not batch:
            break
        offset += len(batch)
    return features


def save_raw(features, state_code=STATE_CODE):
    """Save the untouched HUD response to data/raw/ and return the path."""
    path = Path(RAW_DIR) / f"hud_lihtc_{state_code}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(features, indent=2))
    return path


def clean_lihtc(features):
    df = pd.DataFrame([f["attributes"] for f in features])
    df.rename(columns=LIHTC_FIELDS, inplace=True)
    for c in UNIT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop_duplicates(subset="hud_id").sort_values(["city", "project"])

    df["age_restricted"] = ""         # "55+", "62+", or blank
    df["restricted_units"] = pd.NA    # units set aside, if partial
    df["restriction_source"] = ""     # WHEDA / assessor / property site
    return df.reset_index(drop=True)


def pull_lihtc_rock():
    features = pull_lihtc()
    print(f"Saved raw -> {save_raw(features)}")
    return clean_lihtc(features)


if __name__ == "__main__":
    df = pull_lihtc_rock()
    df.to_excel("hud_lihtc_rock.xlsx", index=False)
    print(df[["project", "city", "total_units", "low_income_units"]])