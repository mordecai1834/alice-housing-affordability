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
    Combine Census estimates and margins of error into one column:
    Estimate (Low-High).

    Preserve geographic columns and use Census metadata for
    readable column names.
    """

    # Geographic columns that must be preserved
    geo_columns = ["GEO_ID", "NAME", "state", "county"]

    # 1. Validate the input DataFrame

    missing_geo = [
        col for col in geo_columns
        if col not in df.columns
    ]

    if missing_geo:
        raise ValueError(
            f"{table} is missing geographic columns: {missing_geo}"
        )

    # Check for duplicate columns in the original data
    if df.columns.duplicated().any():
        duplicates = df.columns[df.columns.duplicated()].tolist()
        raise ValueError(
            f"{table} contains duplicate input columns: {duplicates}"
        )

    # 2. Filter metadata to actual Census variables

    metadata_df = metadata_df[
        metadata_df["variable_code"].isin(df.columns)
    ].copy()

    # Only accept standard ACS estimate and MOE codes
    metadata_df = metadata_df[
        metadata_df["variable_code"].str.match(
            r"^[A-Z]\d{5}_\d{3}[EM]$",
            na=False
        )
    ].copy()

    # Check that metadata does not contain duplicate codes
    if metadata_df["variable_code"].duplicated().any():
        duplicates = metadata_df.loc[
            metadata_df["variable_code"].duplicated(),
            "variable_code"
        ].tolist()

        raise ValueError(
            f"{table} has duplicate metadata variable codes: {duplicates}"
        )

    # 3. Combine estimates and margins of error

    readable_df = df.copy()

    estimate_codes = [
        code for code in metadata_df["variable_code"]
        if code.endswith("E")
    ]

    moe_columns = []

    for estimate_code in estimate_codes:

        # Find matching margin of error column
        moe_code = estimate_code[:-1] + "M"

        if moe_code not in readable_df.columns:
            print(
                f"Warning: {table} is missing {moe_code}. "
                f"Keeping {estimate_code} as its original estimate."
            )
            continue

        # Convert values to numeric
        estimate = pd.to_numeric(
            readable_df[estimate_code],
            errors="coerce"
        )

        moe = pd.to_numeric(
            readable_df[moe_code],
            errors="coerce"
        )

        # Replace Census missing-value codes
        estimate = estimate.replace(
            MISSING_CODES, float("nan")
        )

        moe = moe.replace(
            MISSING_CODES, float("nan")
        )

        # Calculate lower and upper bounds
        low = estimate - moe
        high = estimate + moe

        # Combine into Estimate (Low-High)
        readable_df[estimate_code] = [
            f"{e:g} ({l:g}-{h:g})"
            if pd.notna(e) and pd.notna(l) and pd.notna(h)
            else None
            for e, l, h in zip(estimate, low, high)
        ]

        # Track MOE column for removal
        moe_columns.append(moe_code)

    # Remove original MOE columns
    readable_df = readable_df.drop(
        columns=moe_columns,
        errors="ignore"
    )

    # 4. Keep geographic and estimate columns only

    keep_columns = geo_columns + estimate_codes

    readable_df = readable_df[
        [col for col in keep_columns if col in readable_df.columns]
    ].copy()
    # 5. Rename columns using Census metadata

    column_mapping = {}

    estimate_metadata = metadata_df[
        metadata_df["variable_code"].str.endswith("E")
    ]

    for _, row in estimate_metadata.iterrows():

        code = row["variable_code"]
        label = row["label"]
        concept = row["concept"]

        if pd.notna(label) and pd.notna(concept):

            # Remove parentheses and everything inside them
            concept = concept.split(" (")[0]

            # Replace Census label separators
            readable_label = label.replace("!!", " - ")

            # Remove redundant Estimate prefix
            readable_label = readable_label.removeprefix(
                "Estimate - "
            )

            # Construct readable column name
            readable_name = (
                f"{concept} - {readable_label} [{code}]"
            )

            column_mapping[code] = readable_name

    readable_df = readable_df.rename(
        columns=column_mapping
    )
    # 6. Validate final column names

    if readable_df.columns.duplicated().any():
        duplicates = readable_df.columns[
            readable_df.columns.duplicated()
        ].tolist()

        raise ValueError(
            f"{table} produced duplicate readable columns: {duplicates}"
        )

    # 7. Save readable CSV


    output_path = (
        Path(RAW_DIR) /
        f"acs5_{year}_{table}_readable.csv"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    readable_df.to_csv(output_path, index=False)

    print(
        f"{table}: {len(readable_df)} rows, "
        f"{len(readable_df.columns)} columns"
    )
    print(f"Readable CSV saved: {output_path}")

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