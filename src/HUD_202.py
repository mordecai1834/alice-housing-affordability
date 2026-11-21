import json
from pathlib import Path

import pandas as pd
import requests

from config import RAW_DIR

MF_URL = ("https://egis.hud.gov/arcgis/rest/services/gotit/"
          "MultifamilyProperties/MapServer/0/query")
STATE_CODE = "WI"

ROCK_COUNTY_CITIES = [
    "JANESVILLE", "BELOIT", "EDGERTON", "EVANSVILLE", "MILTON",
    "CLINTON", "FOOTVILLE", "ORFORDVILLE",
]

# HUD field -> our column name
MF_FIELDS = {
    "PROPERTY_ID":                "property_id",
    "PROPERTY_NAME_TEXT":         "project",
    "STD_ADDR":                   "address",
    "STD_CITY":                   "city",
    "STD_ST":                     "state",
    "STD_ZIP5":                   "zip5",
    "TOTAL_UNIT_COUNT":           "total_units",
    "TOTAL_ASSISTED_UNIT_COUNT":  "assisted_units",
    "PROPERTY_CATEGORY_NAME":     "property_category",
    "CLIENT_GROUP_NAME":          "client_group",
    "SOACODE1":                   "section_of_act",
}

UNIT_COLS = ["total_units", "assisted_units"]


def pull_mf(state_code=STATE_CODE, cities=ROCK_COUNTY_CITIES, page_size=1000):
    city_list = ",".join(f"'{c}'" for c in cities)
    where = f"STD_ST='{state_code}' AND UPPER(STD_CITY) IN ({city_list})"
    features, offset = [], 0

    while True:
        params = {
            "where": where,
            "outFields": ",".join(MF_FIELDS),
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "json",
        }
        resp = requests.get(MF_URL, params=params, timeout=60)
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


def save_raw_mf(features, state_code=STATE_CODE):
    """Save the untouched HUD response to data/raw/ and return the path."""
    path = Path(RAW_DIR) / f"hud_multifamily_{state_code}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(features, indent=2))
    return path


def clean_mf(features):
    df = pd.DataFrame([f["attributes"] for f in features])
    df.rename(columns=MF_FIELDS, inplace=True)
    for c in UNIT_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.drop_duplicates(subset="property_id").sort_values(["city", "project"])
    return df.reset_index(drop=True)


def pull_hud_202():
    features = pull_mf()
    print(f"Saved raw -> {save_raw_mf(features)}")
    return clean_mf(features)


if __name__ == "__main__":
    df = pull_hud_202()
    df.to_excel("hud_multifamily_rock.xlsx", index=False)
    print(df[["project", "city", "total_units", "assisted_units"]])

    # Which values mark Section 202 / elderly? Check these before filtering.
    for col in ["section_of_act", "client_group", "property_category"]:
        print(f"\n{col}:\n{df[col].value_counts(dropna=False)}")