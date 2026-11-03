"""Reusable Census ACS 5-year pull (FERC-6)."""
from pathlib import Path
from census_table_meta_data import TABLE_METADATA
import json
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
ALL_TABLES = CORE_TABLES + QUALITY_SIZE_TABLES
# Census "no data" codes that must never be treated as real numbers
MISSING_CODES = [-666666666, -999999999, -888888888, -222222222, -333333333, -555555555]


def pull_acs_table(table, year=ACS_YEAR, state=STATE_FIPS):
    """Pull one whole ACS table (estimates + margins of error) for every
    county in a state. Returns the data exactly as Census sent it (text)."""
    params = {
        "get": f"NAME,group({table})",
        "for": "county:*",
        "in": f"state:{state}",
        "key": CENSUS_API_KEY,
        "descriptive": "true",
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

def get_table_metadata(table, year=ACS_YEAR):
    """
    Retrieve variable labels and concepts for a specific ACS table.
    """
    url = f"https://api.census.gov/data/{year}/acs/acs5/groups/{table}.json"

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    variables = response.json()["variables"]

    metadata = {
        code: {
            "label": details.get("label"),
            "concept": details.get("concept"),
        }
        for code, details in variables.items()
    }

    metadata_df = pd.DataFrame.from_dict(metadata, orient="index")
    metadata_df.index.name = "variable_code"

    return metadata_df.reset_index()

def save_readable_csv(df, metadata_df, table, year=ACS_YEAR):
    """
    Rename Census data columns using the table concept and variable label.
    Preserve geographic identifier columns.
    """

    # Geographic columns that must keep their original names
    geo_columns = ["GEO_ID", "NAME", "state", "county"]

    # Only use metadata for actual data columns
    metadata_df = metadata_df[
        metadata_df["variable_code"].isin(df.columns)
        & ~metadata_df["variable_code"].isin(geo_columns)
    ].copy()

    column_mapping = {}

    for _, row in metadata_df.iterrows():

        code = row["variable_code"]
        label = row["label"]
        concept = row["concept"]

        if pd.notna(label) and pd.notna(concept):

            readable_label = label.replace("!!", " - ")

            # Remove redundant Estimate prefix
            readable_label = readable_label.removeprefix("Estimate - ")

            readable_name = f"{concept} - {readable_label} [{code}]"

            column_mapping[code] = readable_name

    # Rename only ACS variables
    readable_df = df.rename(columns=column_mapping).copy()

    # Save readable CSV
    output_path = Path(RAW_DIR) / f"acs5_{year}_{table}_readable.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    readable_df.to_csv(output_path, index=False)

    # Save metadata separately
    metadata_path = Path(RAW_DIR) / f"acs5_{year}_{table}_metadata.csv"
    metadata_df.to_csv(metadata_path, index=False)

    print(f"Readable CSV saved: {output_path}")
    print(f"Metadata CSV saved: {metadata_path}")

    return readable_df

def make_all_tables_readable(tables=ALL_TABLES, year=ACS_YEAR):
    """
    Process all existing Census CSV files, retrieve their metadata,
    rename their columns, and save readable versions.
    """

    results = {}

    for table in tables:
        print(f"\nProcessing {table}...")

        # Locate existing CSV
        input_path = Path(RAW_DIR) / f"acs5_{year}_{table}.csv"

        if not input_path.exists():
            print(f"Skipping {table}: CSV file not found.")
            continue

        # Read existing CSV
        df = pd.read_csv(input_path, dtype=str)

        # Retrieve metadata
        metadata_df = get_table_metadata(table, year)

        # Apply metadata and save readable CSV
        readable_df = save_readable_csv(df, metadata_df, table, year)

        results[table] = readable_df

    print(f"\nFinished! Processed {len(results)} of {len(tables)} tables.")

    return results

if __name__ == "__main__":
    make_all_tables_readable()