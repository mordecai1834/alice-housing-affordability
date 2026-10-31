from pathlib import Path

import pandas as pd

from config import EXCEL_EXPORT, PROCESSED_DIR


merged_census_table = pd.read_csv(PROCESSED_DIR/"Merge_Census_table.csv")

def excel_export(merged_census_table):

    out_path = Path(EXCEL_EXPORT/ "xlsx_exports.xlsx")
    merged_census_table.to_excel(out_path, index=False)
    print(f"file saved to{out_path}")

if __name__ == "__main__":
    excel_export(merged_census_table)