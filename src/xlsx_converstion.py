from pathlib import Path

import pandas as pd

from config import RAW_DIR
from src import Merge_Census_table
#will have to import the HUD JSON, maybe convert that to csv, or just have serpeate
#functions that output to the same excel file
out_path = Path()
Merge_Census_table.to_excel(out_path, index=False)
print(f"file saved to{out_path}")