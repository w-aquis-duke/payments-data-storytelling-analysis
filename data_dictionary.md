# Data Dictionary

## Raw source fields used

| Source field | Meaning in this project |
| --- | --- |
| `countrynewwb` | Country or aggregate name |
| `codewb` | Three-character country or aggregate code |
| `year` | Survey year |
| `regionwb24_hi` | World Bank region assigned to country rows |
| `incomegroupwb24` | World Bank income classification |
| `group` | Type of population comparison, such as income or gender |
| `group2` | Specific population group, such as richest 60% |
| `merchant_pay` | Share of adults reporting a digital merchant payment, from 0 to 1 |

## `findex_clean.csv`

**Grain:** one country, year, comparison type, and population group.

| Field | Description |
| --- | --- |
| `country` | Country name |
| `country_code` | Three-character country code |
| `year` | 2021 or 2024 |
| `region` | World Bank region |
| `income_group` | World Bank income classification |
| `comparison_group` | `all`, `income`, `urbanicity`, `gender`, `education`, `laborforce`, or `age_cat` |
| `population_group` | The population represented by the row |
| `merchant_pay_pct` | Adults reporting a digital merchant payment, expressed as a percentage |

## `country_payment_changes.csv`

**Grain:** one country.

| Field | Description |
| --- | --- |
| `payment_2021_pct` | National payment-use estimate in 2021 |
| `payment_2024_pct` | National payment-use estimate in 2024 |
| `payment_change_pp` | 2024 minus 2021, in percentage points |
| `payment_increased` | `True` when `payment_change_pp` is greater than zero |
| `payment_change_direction` | Increased, decreased, unchanged, or not comparable |

## `demographic_payment_gaps.csv`

**Grain:** one country, year, and demographic comparison.

| Field | Description |
| --- | --- |
| `comparison` | Short comparison name |
| `comparison_label` | Full human-readable gap definition |
| `first_group` | Group whose rate is the first term in the subtraction |
| `second_group` | Group whose rate is subtracted |
| `first_group_rate_pct` | Payment-use rate for the first group |
| `second_group_rate_pct` | Payment-use rate for the second group |
| `gap_pp` | First-group rate minus second-group rate, in percentage points |
| `complete_pair` | Whether estimates exist for both groups |
| `gap_direction` | Which group has the higher observed rate |

The six comparisons are:

| Comparison | Gap calculation |
| --- | --- |
| Income | Richest 60% minus poorest 40% |
| Urbanicity | Urban minus rural |
| Gender | Men minus women |
| Education | Secondary education or more minus primary education or less |
| Labor force | In labor force minus out of labor force |
| Age | Age 25+ minus ages 15–24 |

## `income_gap_changes.csv`

**Grain:** one country.

| Field | Description |
| --- | --- |
| `income_gap_2021_pp` | Income gap in 2021 |
| `income_gap_2024_pp` | Income gap in 2024 |
| `income_gap_change_pp` | 2024 gap minus 2021 gap |
| `income_gap_widened` | `True` when the income gap increased |
| `income_gap_change_direction` | Widened, narrowed, unchanged, or not comparable |
| `payment_change_pp` | National payment-use change over the same period |
| `growth_third` | Slowest, middle, or fastest third by payment-use change |

## Result tables

| File | Contents |
| --- | --- |
| `key_statistics.csv` | Core infographic numbers and additional descriptive statistics |
| `country_rankings.csv` | Country payment rates, changes, and simple ranks |
| `subgroup_summary.csv` | Coverage, median gap, range, and direction counts for all six comparisons |
| `regional_summary.csv` | Unweighted country summaries by World Bank region |
