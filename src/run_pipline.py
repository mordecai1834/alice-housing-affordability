import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from config import ALL_TABLES
from census_pull import make_all_tables_readable, pull_tables
from HUD_pull import pull_fmr
from Merge_Census_table import (
    merge_census_tables,
    merge_house_descriptive_tables,
)
from merge_2024_annual_by_area import build_wi_qcew
from xlsx_converstion import excel_export, load_sources


def run_pipeline():
    """Run the complete data ingestion and export pipeline."""
    # 1. Pull source data.
    pull_tables(ALL_TABLES)
    pull_fmr()
    build_wi_qcew()

    # 2. Convert Census source tables to readable CSV files.
    make_all_tables_readable(ALL_TABLES)

    # 3. Merge Census tables on GEO_ID.
    merge_census_tables()
    merge_house_descriptive_tables()

    # 4. Export the processed and raw sources to Excel.
    table_tabs, excel_tabs = load_sources()
    excel_export(table_tabs, excel_tabs)


if __name__ == "__main__":
    run_pipeline()