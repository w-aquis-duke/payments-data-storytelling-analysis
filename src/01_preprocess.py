"""Clean the World Bank Global Findex data used in this project.

Run from the project root:
    python src/01_preprocess.py

The script keeps country observations from 2021 and 2024. Missing survey
estimates remain missing; they are never filled with zero.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "global_findex_2025.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "findex_clean.csv"

YEARS = [2021, 2024]
GROUPS = [
    "all",
    "income",
    "urbanicity",
    "gender",
    "education",
    "laborforce",
    "age_cat",
]

SOURCE_COLUMNS = [
    "countrynewwb",
    "codewb",
    "year",
    "regionwb24_hi",
    "incomegroupwb24",
    "group",
    "group2",
    "merchant_pay",
]

RENAMED_COLUMNS = {
    "countrynewwb": "country",
    "codewb": "country_code",
    "regionwb24_hi": "region",
    "incomegroupwb24": "income_group",
    "group": "comparison_group",
    "group2": "population_group",
}


def main() -> None:
    """Read, validate, and save a compact analysis-ready table."""
    data = pd.read_csv(
        RAW_FILE,
        encoding="ISO-8859-2",
        usecols=SOURCE_COLUMNS,
        na_values=["NA"],
        low_memory=False,
    )

    data = data.loc[
        data["year"].isin(YEARS) & data["group"].isin(GROUPS)
    ].copy()

    # Aggregate rows such as "Developing economies" do not have country
    # region or income-group metadata. Requiring both fields leaves countries.
    data = data.loc[
        data["regionwb24_hi"].notna() & data["incomegroupwb24"].notna()
    ].copy()

    data = data.rename(columns=RENAMED_COLUMNS)
    data["merchant_pay"] = pd.to_numeric(data["merchant_pay"], errors="coerce")
    data["merchant_pay_pct"] = data["merchant_pay"] * 100
    data = data.drop(columns="merchant_pay")

    key = [
        "country_code",
        "year",
        "comparison_group",
        "population_group",
    ]
    if data.duplicated(key).any():
        raise ValueError("Duplicate country-year-population rows were found.")

    observed = data["merchant_pay_pct"].dropna()
    if not observed.between(0, 100).all():
        raise ValueError("Payment percentages must fall between 0 and 100.")

    unexpected_groups = set(data["comparison_group"].dropna()) - set(GROUPS)
    if unexpected_groups:
        raise ValueError(f"Unexpected comparison groups: {unexpected_groups}")

    data = data.sort_values(
        ["country", "year", "comparison_group", "population_group"]
    ).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_FILE, index=False)

    print("Preprocessing complete")
    print(f"Rows saved: {len(data):,}")
    print(f"Countries: {data['country_code'].nunique():,}")
    print(f"Years: {sorted(data['year'].unique().tolist())}")
    print(f"Missing payment estimates: {data['merchant_pay_pct'].isna().sum():,}")
    print(f"Output: {OUTPUT_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
