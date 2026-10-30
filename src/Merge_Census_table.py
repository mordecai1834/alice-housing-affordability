from pathlib import Path

import pandas as pd

from config import RAW_DIR,PROCESSED_DIR

RAW_DIR = Path(RAW_DIR)

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

duplicate_columns = ["NAME", "state","county"]
ALL_TABLES = CORE_TABLES + QUALITY_SIZE_TABLES


def merge_census_tables(ALL_TABLES):
    master = None
    for table in ALL_TABLES:
        file_path = RAW_DIR / f"acs5_2024_{table}.csv"

        df = pd.read_csv(file_path)

        if master is None:
            master = df
        else:
            df = df.drop(
                columns = duplicate_columns,
                errors="ignore",
            )
            master = master.merge(df, on= "GEO_ID", how="left", validate="one_to_one")
            print(f"loaded merged table {table}")
    master.to_csv(PROCESSED_DIR / "Merge_Census_table.csv", index=False)
    print(f"file saved to{PROCESSED_DIR}/Merge_Census_table.csv")


if __name__ == "__main__":
    merge_census_tables(ALL_TABLES)
