"""Create country changes and demographic payment-gap features.

Run after preprocessing:
    python src/02_engineer_features.py

A gap is always calculated as the first named group minus the second named
group. For example, the income gap is richest 60% minus poorest 40%.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_FILE = DATA_DIR / "findex_clean.csv"
COUNTRY_OUTPUT = DATA_DIR / "country_payment_changes.csv"
GAP_OUTPUT = DATA_DIR / "demographic_payment_gaps.csv"
INCOME_CHANGE_OUTPUT = DATA_DIR / "income_gap_changes.csv"

# Each gap is first_group minus second_group, in percentage points.
GAP_DEFINITIONS = [
    {
        "comparison": "income",
        "label": "Richest 60% − poorest 40%",
        "first_group": "richest 60%",
        "second_group": "poorest 40%",
    },
    {
        "comparison": "urbanicity",
        "label": "Urban − rural",
        "first_group": "urban",
        "second_group": "rural",
    },
    {
        "comparison": "gender",
        "label": "Men − women",
        "first_group": "men",
        "second_group": "women",
    },
    {
        "comparison": "education",
        "label": "Secondary education or more − primary or less",
        "first_group": "secondary edu or more",
        "second_group": "prim edu or less",
    },
    {
        "comparison": "laborforce",
        "label": "In labor force − out of labor force",
        "first_group": "in laborforce",
        "second_group": "out of laborforce",
    },
    {
        "comparison": "age",
        "source_group": "age_cat",
        "label": "Age 25+ − ages 15–24",
        "first_group": "age 25+",
        "second_group": "ages 15-24",
    },
]


def describe_gap_direction(value: float) -> str:
    """Return which of two demographic groups has the higher rate."""
    if pd.isna(value):
        return "not comparable"
    if value > 0:
        return "first group higher"
    if value < 0:
        return "second group higher"
    return "no gap"


def describe_payment_change(value: float) -> str:
    """Describe a country's national payment-use change."""
    if pd.isna(value):
        return "not comparable"
    if value > 0:
        return "increased"
    if value < 0:
        return "decreased"
    return "unchanged"


def describe_income_gap_change(value: float) -> str:
    """Describe whether a country's income gap widened or narrowed."""
    if pd.isna(value):
        return "not comparable"
    if value > 0:
        return "widened"
    if value < 0:
        return "narrowed"
    return "unchanged"


def build_country_changes(data: pd.DataFrame) -> pd.DataFrame:
    """Put each country's 2021 and 2024 national estimates on one row."""
    country = data.loc[data["comparison_group"] == "all"].copy()
    country = country.pivot(
        index=["country", "country_code", "region", "income_group"],
        columns="year",
        values="merchant_pay_pct",
    ).reset_index()
    country.columns.name = None
    country = country.rename(
        columns={2021: "payment_2021_pct", 2024: "payment_2024_pct"}
    )

    country["payment_change_pp"] = (
        country["payment_2024_pct"] - country["payment_2021_pct"]
    )
    country["payment_increased"] = country["payment_change_pp"].gt(0).where(
        country["payment_change_pp"].notna()
    )
    country["payment_change_direction"] = country["payment_change_pp"].apply(
        describe_payment_change
    )
    return country.sort_values("country").reset_index(drop=True)


def build_gap_table(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate all six within-country demographic gaps."""
    tables = []

    for definition in GAP_DEFINITIONS:
        source_group = definition.get("source_group", definition["comparison"])
        subset = data.loc[data["comparison_group"] == source_group].copy()

        wide = subset.pivot(
            index=["country", "country_code", "year", "region", "income_group"],
            columns="population_group",
            values="merchant_pay_pct",
        ).reset_index()
        wide.columns.name = None

        first = definition["first_group"]
        second = definition["second_group"]
        if first not in wide.columns or second not in wide.columns:
            raise ValueError(f"Missing expected groups for {definition['comparison']}.")

        result = wide[
            ["country", "country_code", "year", "region", "income_group"]
        ].copy()
        result["comparison"] = definition["comparison"]
        result["comparison_label"] = definition["label"]
        result["first_group"] = first
        result["second_group"] = second
        result["first_group_rate_pct"] = wide[first]
        result["second_group_rate_pct"] = wide[second]
        result["gap_pp"] = (
            result["first_group_rate_pct"] - result["second_group_rate_pct"]
        )
        result["complete_pair"] = result["gap_pp"].notna()
        result["gap_direction"] = result["gap_pp"].apply(describe_gap_direction)
        tables.append(result)

    gaps = pd.concat(tables, ignore_index=True)
    return gaps.sort_values(["comparison", "year", "country"]).reset_index(drop=True)


def build_income_gap_changes(
    gaps: pd.DataFrame, country_changes: pd.DataFrame
) -> pd.DataFrame:
    """Compare each country's income gap in 2021 and 2024."""
    income = gaps.loc[gaps["comparison"] == "income"].copy()
    income = income.pivot(
        index=["country", "country_code", "region", "income_group"],
        columns="year",
        values="gap_pp",
    ).reset_index()
    income.columns.name = None
    income = income.rename(
        columns={2021: "income_gap_2021_pp", 2024: "income_gap_2024_pp"}
    )
    income["income_gap_change_pp"] = (
        income["income_gap_2024_pp"] - income["income_gap_2021_pp"]
    )
    income["income_gap_widened"] = income["income_gap_change_pp"].gt(0).where(
        income["income_gap_change_pp"].notna()
    )
    income["income_gap_change_direction"] = income["income_gap_change_pp"].apply(
        describe_income_gap_change
    )

    payment_columns = ["country_code", "payment_change_pp"]
    income = income.merge(
        country_changes[payment_columns], on="country_code", how="left"
    )
    income["growth_third"] = pd.NA

    comparable = income.dropna(
        subset=["income_gap_change_pp", "payment_change_pp"]
    ).sort_values(["payment_change_pp", "country"])

    third_labels = [
        "slowest-growing third",
        "middle third",
        "fastest-growing third",
    ]
    income.loc[comparable.index, "growth_third"] = pd.qcut(
        range(1, len(comparable) + 1), q=3, labels=third_labels
    ).astype("string").to_numpy()

    return income.sort_values("country").reset_index(drop=True)


def main() -> None:
    """Build and save all engineered features."""
    data = pd.read_csv(INPUT_FILE)
    country_changes = build_country_changes(data)
    gaps = build_gap_table(data)
    income_changes = build_income_gap_changes(gaps, country_changes)

    country_changes.to_csv(COUNTRY_OUTPUT, index=False)
    gaps.to_csv(GAP_OUTPUT, index=False)
    income_changes.to_csv(INCOME_CHANGE_OUTPUT, index=False)

    print("Feature engineering complete")
    print(f"Country rows: {len(country_changes):,}")
    print(f"Demographic gap rows: {len(gaps):,}")
    print(
        "Comparable income-gap changes: "
        f"{income_changes['income_gap_change_pp'].notna().sum():,}"
    )
    print(f"Outputs: {DATA_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
