import re
from pathlib import Path

import pandas as pd

from config import EXCEL_EXPORT, PROCESSED_DIR, RAW_DIR


def read_excel_all_sheets(path, prefix):
    """Read EVERY sheet of an Excel file as-is (no header guessing), so title
    rows and notes are kept. Returns {tab_name: DataFrame}."""
    sheets = pd.read_excel(path, sheet_name=None, header=None)
    return {f"{prefix}_{sheet}": df for sheet, df in sheets.items()}


def safe_sheet_name(name, used):
    """Excel tab names: max 31 chars, no [ ] : * ? / \\, and must be unique."""
    name = re.sub(r"[\[\]:*?/\\]", "_", name)[:31]
    base, i = name, 2
    while name.lower() in used:
        suffix = f"_{i}"
        name = base[: 31 - len(suffix)] + suffix
        i += 1
    used.add(name.lower())
    return name


def load_sources():
    # CSV / JSON sources: normal tables with a header row
    table_tabs = {
        "Merged_Census": pd.read_csv(PROCESSED_DIR / "Merge_Census_table.csv"),
        "PMMS_History": pd.read_csv(RAW_DIR / "PMMS_history.csv"),
        "ACS5_2024_B19001": pd.read_csv(RAW_DIR / "acs5_2024_B19001.csv"),
        "HUD_FMR_2027": pd.read_json(RAW_DIR / "hud_fmr_2027_WI.json"),
        "house_hold_descriptive": pd.read_csv(
            PROCESSED_DIR / "Merge_house_hold_descriptive_variables.csv"),
        "bls_qcew_2024_wi": pd.read_csv(PROCESSED_DIR / "bls_qcew_2024_wi_counties.csv"),
    }

    # Excel sources: keep ALL sheets, one tab per sheet
    excel_tabs = {}
    excel_tabs.update(read_excel_all_sheets(RAW_DIR / "cbrfdirexcel.xlsx", "CBRF"))
    excel_tabs.update(read_excel_all_sheets(RAW_DIR / "rcacdirexcel.xlsx", "RCAC"))
    excel_tabs.update(read_excel_all_sheets(RAW_DIR / "HH_Proj_Co_State_2020-2050.xlsx", "DOA_HH_Proj"))
    excel_tabs.update(read_excel_all_sheets(RAW_DIR / "detailed-guidelines-2026.xlsx", "FPL_2026"))
    excel_tabs.update(read_excel_all_sheets(RAW_DIR / "2026 ALICE - Wisconsin Data Sheet.xlsx", "ALICE"))

    return table_tabs, excel_tabs


def excel_export(table_tabs, excel_tabs):
    out_path = Path(EXCEL_EXPORT) / "xlsx_exports.xlsx"
    used = set()

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for name, df in table_tabs.items():
            df.to_excel(writer, sheet_name=safe_sheet_name(name, used), index=False)
        for name, df in excel_tabs.items():
            # header=False because these were read with header=None (raw layout kept)
            df.to_excel(writer, sheet_name=safe_sheet_name(name, used),
                        index=False, header=False)

    print(f"{len(used)} tabs saved to {out_path}")


if __name__ == "__main__":
    table_tabs, excel_tabs = load_sources()
    excel_export(table_tabs, excel_tabs)


