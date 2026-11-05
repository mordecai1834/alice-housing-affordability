from pathlib import Path
import pandas as pd
import census_pull, Merge_Census_table, xlsx_converstion

if __name__ == "__main__":
    #step 1 pull the tables
    census_pull.pull_tables(census_pull.ALL_TABLES)
    #step 2 make them readable
    census_pull.make_all_tables_readable(census_pull.ALL_TABLES)
    #step 3 merge on geoID
    Merge_Census_table.merge_census_tables(census_pull.ALL_TABLES)
    #step 4 export them to excel format
    xlsx_converstion.excel_export(census_pull.ALL_TABLES)