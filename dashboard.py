import streamlit as st
import sqlite3
import os
import subprocess
from analysis import (
    calculate_frequencies,
    create_summary,
    filter_melanoma_miraclib_pbmc,
    plot_response_boxplots,
    compute_statistics,
    analyze_baseline_samples
)

# Build database if it doesn't exist (for Streamlit Cloud deployment)
if not os.path.exists("cell_count.db"):
    subprocess.run(["python", "load_data.py"], check=True)
    subprocess.run(["python", "analysis.py"], check=True)

# Utility function to display DataFrames with index starting at 1
def display_df(df):
    display = df.reset_index(drop=True)
    display.index = display.index + 1
    return display

# Page configuration
st.set_page_config(
    page_title="Immune Cell Population Analysis",
    layout="wide"
)

# Navigation
page = st.segmented_control(
    "Navigation",
    ["Overview", "Statistical Analysis", "Baseline Subset Analysis"],
    default="Overview",
    label_visibility="collapsed"
)
if page is None:
    page = "Overview"

# Load data once and cache it
@st.cache_data
def load_data():
    conn = sqlite3.connect("cell_count.db")
    freq_df = calculate_frequencies(conn)
    summary_df = create_summary(freq_df)
    melanoma_miraclib_pbmc_df = filter_melanoma_miraclib_pbmc(freq_df)
    figures = plot_response_boxplots(melanoma_miraclib_pbmc_df)
    stats_df = compute_statistics(melanoma_miraclib_pbmc_df)
    baseline_df, samples_per_project, responders_non_responders, males_females = analyze_baseline_samples(conn)
    conn.close()
    return freq_df, summary_df, melanoma_miraclib_pbmc_df, figures, stats_df, baseline_df, samples_per_project, responders_non_responders, males_females

freq_df, summary_df, melanoma_miraclib_pbmc_df, figures, stats_df, baseline_df, samples_per_project, responders_non_responders, males_females = load_data()

# Page routing
if page == "Overview":
    st.title("Immune Cell Population Analysis")
    st.markdown("Clinical trial analysis of immune cell populations across multiple patient cohorts, including melanoma and carcinoma patients as well as healthy controls. Samples include both PBMC and whole blood across two treatment arms: miraclib and phauximab.")
    
    # Key metrics row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Samples", freq_df["sample"].nunique())
    col2.metric("Total Subjects", freq_df["subject"].nunique())
    col3.metric("Cell Populations", freq_df["population"].nunique())
    
    # Summary table
    st.subheader("Relative Frequency Summary Table")
    st.dataframe(display_df(summary_df), use_container_width=True)
    
elif page == "Statistical Analysis":
    st.title("Statistical Analysis")
    st.markdown("Comparison of immune cell population relative frequencies between responders and non-responders in melanoma patients treated with miraclib (PBMC samples only).")

    # Boxplot section
    st.subheader("Responders vs Non-Responders by Cell Population")
    
    # Population selector
    populations = melanoma_miraclib_pbmc_df["population"].unique().tolist()
    selected_pop = st.selectbox("Select Cell Population", populations)

    # Filter and plot selected population
    fig = figures[selected_pop]
    stats_row = stats_df[stats_df["population"] == selected_pop].iloc[0]

    plot_col, stats_col = st.columns([3, 1])

    with plot_col:
        st.plotly_chart(fig, use_container_width=True)

    with stats_col:
        st.markdown("**Mann-Whitney U Test**")
        if stats_row["significant"]:
            st.success(f"p = {stats_row['p_value']} (significant)")
        else:
            st.info(f"p = {stats_row['p_value']} (not significant)")
        st.metric("Responders median", f"{stats_row['responders_median']}%")
        st.metric("Non-responders median", f"{stats_row['non_responders_median']}%")
        st.caption(f"U statistic: {stats_row['statistic']} · Significance threshold: p < 0.05")
    
elif page == "Baseline Subset Analysis":
    st.title("Baseline Subset Analysis")
    st.markdown("""
        This analysis identifies all **melanoma PBMC samples at baseline** (day 0) from patients 
        treated with **miraclib**. The subset is used to explore early treatment characteristics 
        across projects, response groups, and demographics.
    """)

    # Baseline samples table
    st.subheader(f"Baseline Samples (n = {baseline_df.shape[0]})")
    st.dataframe(display_df(baseline_df), use_container_width=True)

    # Three column breakdowns
    st.subheader("Subset Breakdowns")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Samples per project**")
        st.dataframe(samples_per_project, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Responders vs non-responders**")
        st.dataframe(responders_non_responders, use_container_width=True, hide_index=True)

    with col3:
        st.markdown("**Males vs females**")
        st.dataframe(males_females, use_container_width=True, hide_index=True)