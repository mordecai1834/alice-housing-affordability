from pathlib import Path

import pandas as pd

from config import RAW_DIR


def convert_xlsx_to_csv(xlsx_path, output_dir=None):
    """Export each worksheet in an Excel workbook to its own CSV file.

    CSV files are named ``<workbook>_<worksheet>.csv``. By default, they are
    written to the raw data directory. Returns the paths of the files created.
    """
    xlsx_path = Path(xlsx_path)
    if not xlsx_path.is_file():
        raise FileNotFoundError(f"Excel workbook not found: {xlsx_path}")

    output_dir = Path(output_dir) if output_dir is not None else Path(RAW_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_paths = []
    with pd.ExcelFile(xlsx_path) as workbook:
        for sheet_name in workbook.sheet_names:
            dataframe = pd.read_excel(workbook, sheet_name=sheet_name)
            csv_path = output_dir / f"{xlsx_path.stem}_{sheet_name}.csv"
            dataframe.to_csv(csv_path, index=False)
            csv_paths.append(csv_path)

    return csv_paths