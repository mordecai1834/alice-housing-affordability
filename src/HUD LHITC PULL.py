import json
from pathlib import Path

import requests

from config import RAW_DIR

MF_URL = ("https://egis.hud.gov/arcgis/rest/services/gotit/"
          "MultifamilyProperties/MapServer/0/query")
STATE_CODE = "WI"

ROCK_COUNTY_CITIES = [
    "JANESVILLE", "BELOIT", "EDGERTON", "EVANSVILLE", "MILTON",
    "CLINTON", "FOOTVILLE", "ORFORDVILLE",
]


def pull_mf_raw(state_code=STATE_CODE, cities=ROCK_COUNTY_CITIES, page_size=1000):
    city_list = ",".join(f"'{c}'" for c in cities)
    where = f"STD_ST='{state_code}' AND UPPER(STD_CITY) IN ({city_list})"
    features, offset = [], 0
    while True:
        params = {
            "where": where,
            "outFields": "*",
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "json",
        }
        resp = requests.get(MF_URL, params=params, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"HUD error {resp.status_code}: {resp.text[:200]}")
        payload = resp.json()
        if "error" in payload:
            raise RuntimeError(f"HUD query error: {payload['error']}")

        batch = payload.get("features", [])
        features.extend(batch)
        if not payload.get("exceededTransferLimit") or not batch:
            break
        offset += len(batch)
    return features


if __name__ == "__main__":
    features = pull_mf_raw()
    path = Path(RAW_DIR) / "hud_multifamily_WI_rock_raw.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(features, indent=2))
    print(f"{len(features)} features -> {path}")
    if features:
        print(list(features[0]["attributes"].keys()))