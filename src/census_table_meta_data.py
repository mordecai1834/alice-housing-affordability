"""ACS 5-year table metadata for the ALICE Housing Affordability Field Guide (v2.2).

table_name   :  is pulled from data element in field guide provided to me by russ
category     : Core / Quality-Size, matching CORE_TABLES and QUALITY_SIZE_TABLES in census_pull.py
"""

TABLE_METADATA = {
    # Core tables
    "B19001": {
        "table_name": "Household count by income bracket",
        "data_element": "4 - Household count by income bracket",
        "purpose": "ALICE count",
    },
    "B19037": {
        "table_name": "Household count by age of householder × income",
        "data_element": "5 - Household count by age of householder x income",
        "purpose": "Age-split demand",
    },
    "B25063": {
        "table_name": "Gross rent distribution",
        "data_element": "9 - Gross rent distribution",
        "purpose": "Rental supply distribution",
    },
    "B25087": {
        "table_name": "Monthly owner costs by mortgage status (bracket counts)",
        "data_element": "10 - Monthly owner costs with mortgage",
        "purpose": "Owner supply distribution",
    },
    "B25088": {
        "table_name": "Median monthly owner costs by mortgage status",
        "data_element": "10 - Monthly owner costs with mortgage",
        "purpose": "Owner supply distribution",
    },
    "B25007": {
        "table_name": "Tenure by age of householder",
        "data_element": "11 - Owner costs by age of householder; 12 - Renter costs by age of householder",
        "purpose": "Age-split supply",
    },
    "B25027": {
        "table_name": "Mortgage status by age",
        "data_element": "13 - Mortgage status by age",
        "purpose": "Owner-supply correction",
    },
    "B25093": {
        "table_name": "Owner costs as % of income, by age of householder",
        "data_element": "11 - Owner costs by age of householder",
        "purpose": "Owner cost-burden",
    },
    "B25072": {
        "table_name": "Gross rent as % of income, by age of householder",
        "data_element": "12 - Renter costs by age of householder",
        "purpose": "Age-split rental burden",
    },
    # Quality tables
    "B25041": {
        "table_name": "Units by number of bedrooms",
        "data_element": "14 - Units by number of bedrooms",
        "purpose": "Unit-size inventory",
    },
    "B25034": {
        "table_name": "Units by year built",
        "data_element": "15 - Units by year built",
        "purpose": "Quality proxy",
    },
    "B25047": {
        "table_name": "Plumbing facilities",
        "data_element": "16 - Units with incomplete plumbing/kitchen",
        "purpose": "Quality filter",
    },
    "B25051": {
        "table_name": "Kitchen facilities",
        "data_element": "16 - Units with incomplete plumbing/kitchen",
        "purpose": "Quality filter",
    },
    "B25014": {
        "table_name": "Overcrowding (persons per room)",
        "data_element": "17 - Overcrowding (persons per room)",
        "purpose": "Quality filter",
    },
}