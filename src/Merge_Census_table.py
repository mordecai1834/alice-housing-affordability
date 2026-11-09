from pathlib import Path

import pandas as pd

from config import RAW_DIR,PROCESSED_DIR, HOUSE_HOLD_DESCRIPTIVE_VARIABLES, CORE_QUALITY_TABLES

RAW_DIR = Path(RAW_DIR)


#Columns that each table has causing duplicate errors, they are to be ignored
duplicate_columns = ["NAME","NAME.1","state","county"]


def merge_census_tables(CORE_QUALITY_TABLES):
    master = None
    for table in CORE_QUALITY_TABLES:
        file_path = RAW_DIR / f"acs5_2024_{table}_readable.csv"

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

def merge_house_descriptive_tables(HOUSE_HOLD_DESCRIPTIVE_VARIABLES):
    master = None
    for table in HOUSE_HOLD_DESCRIPTIVE_VARIABLES:
        file_path = RAW_DIR / f"acs5_2024_{table}_readable.csv"

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
    master.to_csv(PROCESSED_DIR / "Merge_house_hold_descriptive_variables.csv", index=False)
    print(f"file saved to{PROCESSED_DIR}/Merge_Census_table.csv")

if __name__ == "__main__":
    merge_census_tables(CORE_QUALITY_TABLES)
    merge_house_descriptive_tables(HOUSE_HOLD_DESCRIPTIVE_VARIABLES)
