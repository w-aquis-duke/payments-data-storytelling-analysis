# Digital Payments and the Income Gap

This project uses the World Bank Global Findex Database to examine two related
questions:

1. How did reported digital merchant-payment use change between 2021 and 2024?
2. Did within-country demographic gaps narrow as payment use grew?

The analysis identifies patterns in country survey estimates but does not show that payment growth caused any demographic gap to change.

## Dataset

**Source:** World Bank, *Global Findex Database 2025*  
**Download:** [GlobalFindexDatabase2025.csv](https://thedocs.worldbank.org/en/doc/be6615202d1f08a25855c8ac2d615122-0050012025/related/GlobalFindexDatabase2025.csv)

The project uses the `merchant_pay` indicator for adults age 15 or older who
reported making a digital merchant payment. Values are survey estimates stored
as proportions in the raw file and converted to percentages during cleaning.

The raw data contains country, regional, income-level, and demographic summary
rows. This project keeps country rows and never adds demographic rows together.

## Repository structure

```text
payments-data-analysis-submission/
├── data/
│   ├── raw/global_findex_2025.csv
│   └── processed/
├── results/
│   └── figures/
├── src/
│   ├── 01_preprocess.py
│   ├── 02_engineer_features.py
│   └── 03_analyze_and_plot.py
├── .gitignore
├── data_dictionary.md
├── README.md
└── requirements.txt
```

## Reproduce the analysis

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python src/01_preprocess.py
python src/02_engineer_features.py
python src/03_analyze_and_plot.py
```

The final script writes CSV results to `results/` and saves each chart as a PNG
under `results/figures/`. The charts use Matplotlib.

## What each script does

- `01_preprocess.py` selects the relevant years, removes non-country
  aggregates, converts proportions to percentages, and checks data quality.
- `02_engineer_features.py` calculates national payment changes and six
  within-country demographic gaps.
- `03_analyze_and_plot.py` creates the infographic statistics,
  creates broader descriptive summaries, and
  generates Matplotlib charts.

## Engineered features

- **Payment change:** 2024 national payment rate minus the 2021 rate.
- **Demographic gap:** payment rate for the first named group minus the second
  named group, measured in percentage points.
- **Income-gap change:** 2024 income gap minus the 2021 income gap.
- **Growth third:** countries with comparable data divided into three groups
  based on payment-use change.

See [`data_dictionary.md`](data_dictionary.md) for definitions of every output
field.

## Important limitations

- Global Findex estimates are based on self-reported survey responses.
- Country and subgroup coverage differs across years and comparisons.
- Missing estimates remain missing and are excluded from the relevant calculation; they are never treated as zero.
- Country summaries and regional medians are unweighted. They describe the
  typical observed country, not the typical person worldwide.
- A positive gap describes which group reported higher use. It does not explain
  why the gap exists or whether all members of either group share the pattern.
- Comparisons between payment growth and gap change are descriptive and should
  not be interpreted as causal effects.

## Requirements

- Python 3.10 or later
- pandas
- Matplotlib
