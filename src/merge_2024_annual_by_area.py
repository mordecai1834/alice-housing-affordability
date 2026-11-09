import re
import zipfile
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR

QCEW_ZIP = "2024_annual_by_area.zip"
QCEW_OUT = "bls_qcew_2024_wi_counties.csv"


def build_wi_qcew(zip_name=QCEW_ZIP, out_name=QCEW_OUT):
    """Read Wisconsin county files from the BLS QCEW annual-by-area zip,
    combine them, save to PROCESSED_DIR, and return the DataFrame."""
    zip_path = Path(RAW_DIR) / zip_name

    frames = []
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            # county files for Wisconsin: area code 55001-55141 in the file name
            if re.search(r"\b55\d{3}\b", name) and name.lower().endswith(".csv"):
                with z.open(name) as f:
                    frames.append(pd.read_csv(f, dtype={"area_fips": str}))

    if not frames:
        raise ValueError(f"No Wisconsin county files found in {zip_path}")

    wi_qcew = pd.concat(frames, ignore_index=True)

    # drop the statewide row (55000) and keep real counties
    wi_qcew = wi_qcew[wi_qcew["area_fips"].str.match(r"^55\d{3}$")]
    wi_qcew = wi_qcew[wi_qcew["area_fips"] != "55000"]

    n_counties = wi_qcew["area_fips"].nunique()


    out_path = Path(PROCESSED_DIR) / out_name
    wi_qcew.to_csv(out_path, index=False)
    print(f"{n_counties} counties -> {out_path}")

    return wi_qcew


if __name__ == "__main__":
    build_wi_qcew()