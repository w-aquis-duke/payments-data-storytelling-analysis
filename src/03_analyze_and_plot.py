"""Run descriptive EDA and create PNG charts with Matplotlib.

Run after feature engineering:
    python src/03_analyze_and_plot.py

All comparisons are descriptive. They show country-level patterns and do not
establish why payment use or demographic gaps changed.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURE_DIR = RESULTS_DIR / "figures"

SOURCE_NOTE = "Source: World Bank Global Findex Database 2025. Missing estimates excluded."
BLUE = "#2878D0"
ORANGE = "#F0642E"
GRAY = "#9AA7B5"
BLACK = "#14202E"


def save_chart(fig: plt.Figure, filename: str) -> None:
    """Add the source note and save one PNG chart."""
    fig.text(0.01, 0.01, SOURCE_NOTE, fontsize=9, color="#64748B")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURE_DIR / f"{filename}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def add_stat(
    rows: list[dict],
    section: str,
    statistic: str,
    value: float,
    unit: str,
    sample_size: int | None = None,
) -> None:
    """Append one statistic to the results table."""
    rows.append(
        {
            "section": section,
            "statistic": statistic,
            "value": value,
            "unit": unit,
            "sample_size": sample_size,
        }
    )


def validate_infographic_results(
    latest: pd.DataFrame,
    matched: pd.DataFrame,
    gaps_2024: pd.DataFrame,
    comparable_income: pd.DataFrame,
) -> None:
    """Stop if the core infographic statistics no longer reproduce."""
    income = gaps_2024.loc[gaps_2024["comparison"] == "income"]
    urban = gaps_2024.loc[gaps_2024["comparison"] == "urbanicity"]
    gender = gaps_2024.loc[gaps_2024["comparison"] == "gender"]
    nigeria = income.loc[income["country"] == "Nigeria"].iloc[0]

    assert len(latest) == 98
    assert len(matched) == 74
    assert int(matched["payment_increased"].sum()) == 58
    assert len(income) == 69 and int((income["gap_pp"] > 0).sum()) == 69
    assert len(urban) == 69 and int((urban["gap_pp"] > 0).sum()) == 64
    assert len(gender) == 70 and int((gender["gap_pp"] > 0).sum()) == 60
    assert len(comparable_income) == 43
    assert int((comparable_income["income_gap_change_pp"] > 0).sum()) == 20
    assert int((income["gap_pp"] < nigeria["gap_pp"]).sum()) == 34
    assert int((income["gap_pp"] > nigeria["gap_pp"]).sum()) == 34


def main() -> None:
    """Calculate result tables, validate key claims, and save seven charts."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    country = pd.read_csv(DATA_DIR / "country_payment_changes.csv")
    gaps = pd.read_csv(DATA_DIR / "demographic_payment_gaps.csv")
    income_changes = pd.read_csv(DATA_DIR / "income_gap_changes.csv")

    latest = country.dropna(subset=["payment_2024_pct"]).copy()
    matched = country.dropna(subset=["payment_change_pp"]).copy()
    gaps_2024 = gaps.loc[(gaps["year"] == 2024) & gaps["complete_pair"]].copy()
    comparable_income = income_changes.dropna(
        subset=["income_gap_change_pp", "payment_change_pp"]
    ).copy()

    validate_infographic_results(latest, matched, gaps_2024, comparable_income)

    # ------------------------------------------------------------------
    # Summary tables
    # ------------------------------------------------------------------
    statistics = []
    add_stat(statistics, "coverage", "countries with a 2024 estimate", len(latest), "countries")
    add_stat(statistics, "change", "countries observed in both years", len(matched), "countries")
    add_stat(
        statistics,
        "change",
        "countries with higher payment use in 2024",
        int(matched["payment_increased"].sum()),
        "countries",
        len(matched),
    )
    add_stat(
        statistics,
        "change",
        "median payment change, 2021–2024",
        matched["payment_change_pp"].median(),
        "percentage points",
        len(matched),
    )
    add_stat(
        statistics,
        "adoption",
        "median payment use in 2024",
        latest["payment_2024_pct"].median(),
        "percent of adults",
        len(latest),
    )
    add_stat(
        statistics,
        "adoption",
        "25th percentile payment use in 2024",
        latest["payment_2024_pct"].quantile(0.25),
        "percent of adults",
        len(latest),
    )
    add_stat(
        statistics,
        "adoption",
        "75th percentile payment use in 2024",
        latest["payment_2024_pct"].quantile(0.75),
        "percent of adults",
        len(latest),
    )

    subgroup_summary = (
        gaps_2024.groupby(["comparison", "comparison_label"], as_index=False)
        .agg(
            countries=("country", "count"),
            median_gap_pp=("gap_pp", "median"),
            mean_gap_pp=("gap_pp", "mean"),
            minimum_gap_pp=("gap_pp", "min"),
            maximum_gap_pp=("gap_pp", "max"),
            positive_gap_count=("gap_pp", lambda x: int((x > 0).sum())),
            negative_gap_count=("gap_pp", lambda x: int((x < 0).sum())),
            zero_gap_count=("gap_pp", lambda x: int((x == 0).sum())),
        )
        .sort_values("median_gap_pp", ascending=False)
    )
    subgroup_summary["reverse_or_tied_count"] = (
        subgroup_summary["negative_gap_count"] + subgroup_summary["zero_gap_count"]
    )
    subgroup_summary.to_csv(RESULTS_DIR / "subgroup_summary.csv", index=False)

    for row in subgroup_summary.itertuples():
        add_stat(
            statistics,
            "demographic gaps",
            f"median {row.comparison} gap in 2024",
            row.median_gap_pp,
            "percentage points",
            row.countries,
        )
        add_stat(
            statistics,
            "demographic gaps",
            f"countries with a positive {row.comparison} gap",
            row.positive_gap_count,
            "countries",
            row.countries,
        )

    income_2024 = gaps_2024.loc[gaps_2024["comparison"] == "income"].copy()
    nigeria = income_2024.loc[income_2024["country"] == "Nigeria"].iloc[0]
    add_stat(statistics, "Nigeria example", "poorest 40% payment rate", nigeria.second_group_rate_pct, "percent of adults")
    add_stat(statistics, "Nigeria example", "richest 60% payment rate", nigeria.first_group_rate_pct, "percent of adults")
    add_stat(statistics, "Nigeria example", "income gap", nigeria.gap_pp, "percentage points")

    add_stat(
        statistics,
        "income gap change",
        "countries with comparable income gaps",
        len(comparable_income),
        "countries",
    )
    add_stat(
        statistics,
        "income gap change",
        "countries where the income gap widened",
        int((comparable_income["income_gap_change_pp"] > 0).sum()),
        "countries",
        len(comparable_income),
    )
    add_stat(
        statistics,
        "income gap change",
        "median income-gap change",
        comparable_income["income_gap_change_pp"].median(),
        "percentage points",
        len(comparable_income),
    )

    correlation = comparable_income["payment_change_pp"].corr(
        comparable_income["income_gap_change_pp"]
    )
    add_stat(
        statistics,
        "income gap change",
        "correlation of payment growth and income-gap change",
        correlation,
        "Pearson correlation",
        len(comparable_income),
    )

    third_order = [
        "slowest-growing third",
        "middle third",
        "fastest-growing third",
    ]
    third_summary = (
        comparable_income.groupby("growth_third", as_index=False)
        .agg(
            countries=("country", "count"),
            median_payment_change_pp=("payment_change_pp", "median"),
            median_income_gap_change_pp=("income_gap_change_pp", "median"),
            widened_count=("income_gap_change_pp", lambda x: int((x > 0).sum())),
        )
        .set_index("growth_third")
        .loc[third_order]
        .reset_index()
    )

    for row in third_summary.itertuples():
        add_stat(
            statistics,
            "growth thirds",
            f"{row.growth_third}: median payment change",
            row.median_payment_change_pp,
            "percentage points",
            row.countries,
        )
        add_stat(
            statistics,
            "growth thirds",
            f"{row.growth_third}: median income-gap change",
            row.median_income_gap_change_pp,
            "percentage points",
            row.countries,
        )

    fastest_ten = comparable_income.nlargest(10, "payment_change_pp")
    add_stat(
        statistics,
        "growth thirds",
        "income gaps widened among 10 fastest-growing countries",
        int((fastest_ten["income_gap_change_pp"] > 0).sum()),
        "countries",
        10,
    )

    key_statistics = pd.DataFrame(statistics)
    key_statistics["value"] = key_statistics["value"].round(4)
    key_statistics.to_csv(RESULTS_DIR / "key_statistics.csv", index=False)

    country_rankings = country.copy()
    country_rankings["rank_2024_highest"] = country_rankings[
        "payment_2024_pct"
    ].rank(method="min", ascending=False)
    country_rankings["rank_change_largest"] = country_rankings[
        "payment_change_pp"
    ].rank(method="min", ascending=False)
    country_rankings["top_10_increase"] = country_rankings[
        "rank_change_largest"
    ].le(10).where(country_rankings["payment_change_pp"].notna())
    country_rankings["top_10_decrease"] = country_rankings[
        "payment_change_pp"
    ].rank(method="min", ascending=True).le(10).where(
        country_rankings["payment_change_pp"].notna()
    )
    country_rankings.to_csv(RESULTS_DIR / "country_rankings.csv", index=False)

    regional_summary = (
        latest.groupby("region", as_index=False)
        .agg(
            countries=("country", "count"),
            median_payment_2024_pct=("payment_2024_pct", "median"),
            mean_payment_2024_pct=("payment_2024_pct", "mean"),
            minimum_payment_2024_pct=("payment_2024_pct", "min"),
            maximum_payment_2024_pct=("payment_2024_pct", "max"),
        )
        .sort_values("median_payment_2024_pct", ascending=False)
    )
    regional_summary.to_csv(RESULTS_DIR / "regional_summary.csv", index=False)

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.titlesize": 15,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
        }
    )

    # 1. Distribution of country-level change.
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(matched["payment_change_pp"], bins=18, color=BLUE, edgecolor="white")
    ax.axvline(0, color=BLACK, linewidth=1.5)
    ax.set_title(
        "Most matched countries reported higher payment use by 2024\n"
        f"{int(matched['payment_increased'].sum())} of {len(matched)} increased; "
        f"median change {matched['payment_change_pp'].median():.1f} percentage points",
        loc="left",
    )
    ax.set_xlabel("Change from 2021 to 2024 (percentage points)")
    ax.set_ylabel("Number of countries")
    save_chart(fig, "01_payment_change_distribution")

    # 2. Countries with the largest increases and decreases.
    extremes = pd.concat(
        [matched.nsmallest(10, "payment_change_pp"), matched.nlargest(10, "payment_change_pp")]
    ).drop_duplicates("country_code")
    extremes = extremes.sort_values("payment_change_pp")
    colors = [BLUE if value < 0 else ORANGE for value in extremes["payment_change_pp"]]
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(extremes["country"], extremes["payment_change_pp"], color=colors)
    ax.axvline(0, color=BLACK, linewidth=1.5)
    ax.set_title(
        "The largest country-level changes moved in both directions\n"
        "Ten largest increases and ten largest decreases among matched countries",
        loc="left",
    )
    ax.set_xlabel("Change from 2021 to 2024 (percentage points)")
    ax.set_ylabel("")
    save_chart(fig, "02_largest_country_changes")

    # 3. Country distributions within regions.
    regions = regional_summary["region"].tolist()[::-1]
    region_values = [
        latest.loc[latest["region"] == region, "payment_2024_pct"] for region in regions
    ]
    fig, ax = plt.subplots(figsize=(11, 7))
    boxes = ax.boxplot(
        region_values,
        orientation="horizontal",
        tick_labels=regions,
        patch_artist=True,
    )
    for box in boxes["boxes"]:
        box.set(facecolor="#8CB6E3", edgecolor=BLUE)
    for median_line in boxes["medians"]:
        median_line.set(color=BLUE, linewidth=2)
    ax.set_title(
        "Payment use varies within every region\n"
        "Country estimates; regional summaries are unweighted",
        loc="left",
    )
    ax.set_xlabel("Adults reporting a digital merchant payment in 2024 (%)")
    ax.set_ylabel("")
    ax.set_xlim(0, 100)
    save_chart(fig, "03_regional_payment_distribution")

    # 4. Median gap and direction counts for all six comparisons.
    subgroup_plot = subgroup_summary.sort_values("median_gap_pp")
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(
        subgroup_plot["comparison_label"], subgroup_plot["median_gap_pp"], color=ORANGE
    )
    for bar, row in zip(bars, subgroup_plot.itertuples()):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{row.positive_gap_count} of {row.countries} positive",
            va="center",
        )
    ax.axvline(0, color=BLACK, linewidth=1.5)
    ax.set_xlim(0, subgroup_plot["median_gap_pp"].max() + 8)
    ax.set_title(
        "Income is not the only consistent payment divide\n"
        "Median within-country gap and countries where the first group reports higher use",
        loc="left",
    )
    ax.set_xlabel("Median gap in 2024 (percentage points)")
    ax.set_ylabel("")
    save_chart(fig, "04_demographic_gap_comparison")

    # 5. Income-gap ranking across countries.
    income_plot = income_2024.sort_values("gap_pp")
    y_positions = list(range(len(income_plot)))
    fig, ax = plt.subplots(figsize=(9, 17))
    ax.scatter(income_plot["gap_pp"], y_positions, color=ORANGE, s=28)
    ax.set_yticks(y_positions, income_plot["country"], fontsize=8)
    ax.axvline(0, color=BLACK, linewidth=1.5)
    ax.set_title(
        "Every observed 2024 income gap points in the same direction\n"
        "Richest 60% minus poorest 40%; each dot is one country",
        loc="left",
    )
    ax.set_xlabel("Income gap (percentage points)")
    ax.set_ylabel("")
    save_chart(fig, "05_country_income_gaps")

    # 6. Payment growth compared with income-gap change.
    widened = comparable_income["income_gap_change_pp"] > 0
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        comparable_income.loc[~widened, "payment_change_pp"],
        comparable_income.loc[~widened, "income_gap_change_pp"],
        color=BLUE,
        label="Gap narrowed",
        s=42,
    )
    ax.scatter(
        comparable_income.loc[widened, "payment_change_pp"],
        comparable_income.loc[widened, "income_gap_change_pp"],
        color=ORANGE,
        label="Gap widened",
        s=42,
    )
    ax.axhline(0, color=BLACK, linewidth=1)
    ax.axvline(0, color=BLACK, linewidth=1)
    ax.set_title(
        "Faster payment growth often coincided with widening income gaps\n"
        f"43 matched countries; descriptive Pearson correlation r = {correlation:.2f}",
        loc="left",
    )
    ax.set_xlabel("Payment-use change, 2021–2024 (percentage points)")
    ax.set_ylabel("Income-gap change, 2021–2024 (percentage points)")
    ax.legend(frameon=False)
    save_chart(fig, "06_growth_vs_income_gap_change")

    # 7. Median gap change by payment-growth third.
    colors = [BLUE, GRAY, ORANGE]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(
        third_summary["growth_third"],
        third_summary["median_income_gap_change_pp"],
        color=colors,
    )
    ax.axhline(0, color=BLACK, linewidth=1.5)
    for bar, value in zip(bars, third_summary["median_income_gap_change_pp"]):
        vertical_alignment = "bottom" if value >= 0 else "top"
        offset = 0.12 if value >= 0 else -0.12
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + offset,
            f"{value:+.1f} pp",
            ha="center",
            va=vertical_alignment,
        )
    ax.set_title(
        "The income gap widened most in the fastest-growing third\n"
        "Countries grouped by their change in digital merchant-payment use",
        loc="left",
    )
    ax.set_xlabel("")
    ax.set_ylabel("Median income-gap change (percentage points)")
    save_chart(fig, "07_income_gap_change_by_growth_third")

    print("Analysis complete")
    print("\nCore infographic checks")
    print(f"2024 country estimates: {len(latest)}")
    print(
        f"Matched countries increasing: {int(matched['payment_increased'].sum())} "
        f"of {len(matched)}"
    )
    print(f"Median payment change: {matched['payment_change_pp'].median():.1f} pp")
    print(f"Median 2024 income gap: {income_2024['gap_pp'].median():.1f} pp")
    print(f"Nigeria income gap: {nigeria.gap_pp:.1f} pp")
    print(
        "Comparable income gaps that widened: "
        f"{int((comparable_income['income_gap_change_pp'] > 0).sum())} "
        f"of {len(comparable_income)}"
    )
    print(f"\nTables: {RESULTS_DIR.relative_to(PROJECT_ROOT)}/")
    print(f"PNG charts: {FIGURE_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
