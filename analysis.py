import sqlite3
import pandas as pd
import plotly.express as px
from scipy.stats import mannwhitneyu

def calculate_frequencies(conn):
    query = """
        SELECT
            s.sample,
            s.subject,
            su.condition,
            su.treatment,
            su.response,
            s.sample_type,
            s.time_from_treatment_start,
            c.population,
            c.count,
            SUM(c.count) OVER (PARTITION BY s.sample) AS total_count,
            ROUND(100.0 * c.count / SUM(c.count) OVER (PARTITION BY s.sample), 2) AS percentage
        FROM counts c
        JOIN samples s ON c.sample = s.sample
        JOIN subjects su ON s.subject = su.subject             
    """
    freq_df = pd.read_sql_query(query, conn)

    print(f"Calculated relative frequencies for {freq_df['sample'].nunique()} samples")
    return freq_df

def create_summary(df):
    summary_cols = ["sample", "total_count", "population", "count", "percentage"]
    summary_df = df[summary_cols].copy()
    summary_df.to_csv("output/summary_table.csv", index=False)

    print("Summary table created at output/summary_table.csv")
    return summary_df

def filter_melanoma_miraclib_pbmc(df):
    filtered_df = df[
        (df["condition"] == "melanoma") &
        (df["treatment"] == "miraclib") &
        (df["sample_type"] == "PBMC")
    ].copy()

    print(f"Filtered to {filtered_df['subject'].nunique()} subjects, {filtered_df['sample'].nunique()} samples")
    return filtered_df

def plot_response_boxplots(df, save=False):
    populations = df["population"].unique()
    figures = {}

    for pop in populations:
        plot_df = df[df["population"] == pop]

        fig = px.box(
            plot_df,
            x="response",
            y="percentage",
            color="response",
            labels={"response": "Treatment Response", "percentage": "Relative Frequency (%)"},
            category_orders={"response": ["yes", "no"]}
        )
        fig.update_layout(
            title={
                "text": f"Responders vs Non-Responders ({pop})",
                "x": 0.5,
                "xanchor": "center"
            }
        )
        fig.update_layout(showlegend=False)
        figures[pop] = fig

        if save:
            fig.write_image(f"output/boxplot_{pop}.png")
            print(f"Boxplot saved to output/boxplot_{pop}.png")

    return figures

def compute_statistics(df):
    results = []
    populations = df["population"].unique()

    for pop in populations:
        pop_df = df[df["population"] == pop]
        responders = pop_df[pop_df["response"] == "yes"]["percentage"]
        non_responders = pop_df[pop_df["response"] == "no"]["percentage"]

        stat, p_value = mannwhitneyu(responders, non_responders, alternative="two-sided")
        results.append({
            "population": pop,
            "statistic": round(stat, 4),
            "p_value": round(p_value, 4),
            "responders_median": round(responders.median(), 2),
            "non_responders_median": round(non_responders.median(), 2),
            "significant": p_value < 0.05
        })
    stats_df = pd.DataFrame(results)
    stats_df.to_csv("output/stats_summary.csv", index=False)

    print("Statistical summary saved to output/stats_summary.csv")
    return stats_df

def analyze_baseline_samples(conn):
    # Query 1: Baseline subset -- melanoma subjects treated with miraclib and PBMC samples
    query = """
        SELECT
            s.sample,
            su.subject,
            su.project,
            su.sex,
            su.response
        FROM samples s
        JOIN subjects su ON s.subject = su.subject
        WHERE
            s.sample_type = 'PBMC'
            AND s.time_from_treatment_start = 0
            AND su.condition = 'melanoma'
            AND su.treatment = 'miraclib'
        """
    baseline_df = pd.read_sql_query(query, conn)

    # Distribution of samples across projects
    samples_per_project = baseline_df.groupby("project")["sample"].nunique().reset_index(name="num_samples")
    print("\nSamples per project:")
    print(samples_per_project)

    # Distribution of subjects (responders/non-responders)
    responders_non_responders = baseline_df.groupby("response")["subject"].nunique().reset_index(name="num_subjects")
    print("\nResponders vs Non-Responders:")
    print(responders_non_responders)

    # Distribution of subjects (males/females)
    males_females = baseline_df.groupby("sex")["subject"].nunique().reset_index(name="num_subjects")
    print("\nMales vs Females:")
    print(males_females)

    # Query 2: Melanoma male subjects who responded to treatment at baseline
    query = """
        SELECT
            ROUND(AVG(c.count), 2) AS avg_b_cell
        FROM counts c
        JOIN samples s ON c.sample = s.sample
        JOIN subjects su ON s.subject = su.subject
        WHERE
            c.population = 'b_cell'
            AND s.time_from_treatment_start = 0
            AND su.sex = 'M'
            AND su.condition = 'melanoma'
            AND su.response = 'yes'
        """
    avg_bcell_df = pd.read_sql_query(query, conn)
    avg_bcell = avg_bcell_df["avg_b_cell"].iloc[0]

    print(f"\nAverage B cells (melanoma males, responders, time=0): {avg_bcell}")

def main():
    # Connect to database
    conn = sqlite3.connect("cell_count.db")

    # Calculate relative frequencies of cell populations with SQL query
    freq_df = calculate_frequencies(conn)

    # Create summary table with sample, total count, population, count, and percentage
    summary_df = create_summary(freq_df)
    print(summary_df.head(20))

    # Filter query results to melanoma patients treated with miraclib and PBMC samples
    melanoma_miraclib_pbmc_df = filter_melanoma_miraclib_pbmc(freq_df)

    # Create boxplots comparing responders vs non-responders for each cell population and save as images
    plot_response_boxplots(melanoma_miraclib_pbmc_df, save=True)

    # Perform Mann-Whitney U test comparing responders vs non-responders for each cell population
    stats_df = compute_statistics(melanoma_miraclib_pbmc_df)
    print(stats_df)

    # Query to identify all melanoma PBMC samples at baseline from patients treated with miraclib
    # and address analytical questions about distribution of samples across projects, responders
    analyze_baseline_samples(conn)

    conn.close()
    print("Analysis complete")

if __name__ == "__main__":
    main()
