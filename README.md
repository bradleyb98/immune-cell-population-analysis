# Immune Cell Population Analysis

An end-to-end clinical trial data pipeline and interactive dashboard for analyzing immune cell population frequencies across patient cohorts treated with miraclib and phauximab.

**Live Dashboard:** [link](https://immune-cell-population-analysis.streamlit.app/)

---

## Setup & Usage

### Requirements
- Python 3.12+
- Dependencies listed in `requirements.txt`

### Running the Pipeline

```bash
make setup      # Install dependencies
make pipeline   # Initialize database, load data, run analysis
make dashboard  # Launch interactive dashboard at localhost:8501
```

---

## Project Structure

immune-cell-population-analysis/
├── load_data.py        # Database schema creation and CSV loading (Part 1)
├── analysis.py         # Frequency analysis, statistics, and subset queries (Parts 2-4)
├── dashboard.py        # Interactive Streamlit dashboard
├── Makefile            # Pipeline automation
├── requirements.txt    # Python dependencies
├── data/
│   └── cell-count.csv  # Source data
└── output/
    ├── summary_table.csv
    ├── stats_summary.csv
    └── boxplot_*.png

---

## Database Schema

### Schema Design

Four normalized tables:

- **`projects`** — project-level identifier (`project TEXT PRIMARY KEY`)
- **`subjects`** — subject demographics and trial attributes (`subject`, `project`, `condition`, `age`, `sex`, `treatment`, `response`)
- **`samples`** — sample-level metadata (`sample`, `subject`, `sample_type`, `time_from_treatment_start`)
- **`counts`** — long-format cell population counts (`sample`, `population`, `count`)

### Design Decisions & Rationale

- **Long format for `counts` table:** cell population counts are stored in long format (one row per sample per population) rather than wide format (one column per population). This means 5 rows per sample rather than 1, but eliminates the need to reshape data for downstream analysis as the frequency table (Part 2) and boxplot/statistics (Part 3) both require long-format data natively. Adding new cell populations requires only new rows, not schema changes.

- **`response` and `treatment` on `subjects`:** inspection of the data shows these values are constant across all timepoints for each subject, consistent with them being trial-level outcome assessments rather than per-sample measurements. In an adaptive trial design they might belong on `samples` instead.

- **Composite primary key on `counts`:** `PRIMARY KEY (sample, population)` serves dual purpose — uniquely identifying each row and enforcing the constraint that each sample can only have one count per population.

- **`cell_population` CHECK constraint:** the `counts` table validates known population names at load time (`b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, `monocyte`). Adding new populations requires updating this constraint and rerunning the pipeline — acceptable at current scale but could be replaced with a separate `populations` lookup table in a larger system.

- **`projects` table:** included despite having only one column to enforce referential integrity and provide a natural foundation for project-level metadata (sponsor, start date, therapeutic area) without schema restructuring.

- **`PRAGMA foreign_keys = ON`:** SQLite does not enforce foreign key constraints by default — explicitly enabled in `load_data.py`.

- **`DROP TABLE IF EXISTS` before `CREATE TABLE`:** rerunning `make pipeline` always produces a clean rebuild with no duplicate rows.

- **Nullable `age` and `sex`:** real clinical data may have missing demographics; subjects should remain in the dataset even with incomplete metadata.

### Scaling Considerations

For hundreds of projects and thousands of samples:

- **Long format** means new cell populations = new rows only, no schema migrations
- **Normalization** reduces redundancy — demographics stored once per subject rather than duplicated across every sample row
- **`projects` table** as foundation scales naturally to hundreds of projects without denormalization

---

## Code Structure

### `load_data.py`
Initializes the SQLite database and loads `cell-count.csv`. Key functions:
- `create_tables()` — drops and recreates all four tables with constraints
- `validate_data()` — checks for missing columns, null IDs, duplicate samples, negative counts
- `extract_tables()` — splits wide CSV into normalized dataframes including long-format melt for `counts`
- `insert_data()` — inserts in foreign key order (projects → subjects → samples → counts)

### `analysis.py`
Runs all analytical components with optional save output capacity to `output/`. Key functions:
- `calculate_frequencies()` — SQL window function query computing total count and relative frequency per sample per population
- `create_summary()` — exports 5-column summary table per Part 2 requirements
- `filter_melanoma_miraclib_pbmc()` — filters to melanoma + miraclib + PBMC subset for Part 3
- `plot_response_boxplots()` — generates per-population boxplots comparing responders vs non-responders; optional save functionality disabled in this repository for static plot images; plots pre-saved for reference
- `compute_statistics()` — Mann-Whitney U test per population; reports statistic, p-value, medians, significance
- `analyze_baseline_samples()` — Part 4 subset queries: baseline melanoma PBMC miraclib samples broken down by project, response, and sex; average B cell count for melanoma male responders at time=0

### `dashboard.py`
Interactive Streamlit dashboard with three pages:
- **Overview** — dataset summary metrics and full relative frequency table
- **Statistical Analysis** — interactive population selector with boxplot and Mann-Whitney U results
- **Baseline Subset Analysis** — baseline sample table with breakdowns by project, response, and sex

Auto-builds database on first run if not present (for cloud deployment).

---

## Statistical Analysis Notes

- **Test used:** Mann-Whitney U (non-parametric, two-sided) — appropriate for comparing two independent groups without assuming normal distribution
- **Finding:** cd4_t_cell populations reached statistical significance (p = 0.013) between responders and non-responders; all other populations did not
- **Limitation:** subjects contribute 3 data points each (one per timepoint), meaning observations are not fully independent — a more rigorous analysis would use a mixed effects model accounting for repeated measures. This approach is appropriate for exploratory pattern identification.

---

## Dashboard

[Link to live dashboard](https://immune-cell-population-analysis.streamlit.app/)

To run locally:
```bash
make dashboard
```
Opens at `http://localhost:8501`