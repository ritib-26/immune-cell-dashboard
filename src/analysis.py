"""
Part 2: Analytical functions for Parts 2, 3, and 4.

Run: python analysis.py
"""

import sqlite3
import pandas as pd
from scipy import stats

def get_frequency_table(conn):
    """
    Part 2: calculate relative frequency of each cell population per sample.
    Returns a dataframe with columns: sample, total_count, population, count, percentage.
    """
    query = """
        with totals as (
            -- sum all cell counts per sample
            select sample_id, sum(count) as total_count
            from cell_counts
            group by sample_id
        )
        select
            cc.sample_id                                    as sample,
            t.total_count,
            cc.population,
            cc.count,
            round(100.0 * cc.count / t.total_count, 4)     as percentage
        from cell_counts cc
        join totals t on t.sample_id = cc.sample_id
        order by cc.sample_id, cc.population
    """
    return pd.read_sql_query(query, conn)

def save_frequency_table(df, output_path="outputs/frequency_table.csv"):
    """Save the frequency table to a CSV file."""
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f" Saved {output_path}")


# Part 3
def get_responder_comparison(conn):
    """
    Part 3: filter the Part 2 frequency table to melanoma/miraclib/PBMC
    samples and annotate with response status.
    """
    query = """
        with totals as (
            select sample_id, sum(count) as total_count
            from cell_counts
            group by sample_id
        )
        select
            s.sample_id     as sample,
            su.response,
            cc.population,
            cc.count,
            t.total_count,
            round(100.0 * cc.count / t.total_count, 4) as percentage
        from cell_counts cc
        join totals   t  on t.sample_id   = cc.sample_id
        join samples  s  on s.sample_id   = cc.sample_id
        join subjects su on su.subject_id = s.subject_id
        where lower(s.condition)   = 'melanoma'
          and lower(s.treatment)   = 'miraclib'
          and lower(s.sample_type) = 'pbmc'
          and su.response is not null
        order by s.sample_id, cc.population
    """
    return pd.read_sql_query(query, conn)


def run_statistics(df):
    """
    Mann-Whitney U test per cell population: responders vs non-responders.
    Non-parametric test — appropriate for small clinical cohorts.
    """
    results = []

    for pop, grp in df.groupby("population"):
        responders     = grp.loc[grp["response"] == "yes", "percentage"]
        non_responders = grp.loc[grp["response"] == "no",  "percentage"]

        if len(responders) < 2 or len(non_responders) < 2:
            continue

        u_stat, p_val = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")

        results.append({
            "population":            pop,
            "n_responders":          len(responders),
            "n_non_responders":      len(non_responders),
            "mean_responders":       round(responders.mean(), 3),
            "mean_non_responders":   round(non_responders.mean(), 3),
            "median_responders":     round(responders.median(), 3),
            "median_non_responders": round(non_responders.median(), 3),
            "mannwhitney_u":         round(u_stat, 3),
            "p_value":               round(p_val, 4),
            "significant":           p_val < 0.05,
        })

    return pd.DataFrame(results).sort_values("p_value")

def save_responder_comparison(df, stats_df):
    """Save Part 3 outputs to CSV."""
    import os
    os.makedirs("outputs", exist_ok=True)
    df.to_csv("outputs/responder_comparison.csv", index=False)
    stats_df.to_csv("outputs/statistical_results.csv", index=False)
    print("Saved outputs/responder_comparison.csv")
    print("Saved outputs/statistical_results.csv")


# Part 4
def get_baseline_subset(conn):
    """
    Part 4-i: all melanoma PBMC samples at baseline (day 0) treated with miraclib.
    """
    query = """
        select
            s.sample_id,
            s.project_id,
            s.subject_id,
            s.condition,
            s.treatment,
            s.sample_type,
            s.time_from_treatment_start,
            su.response,
            su.sex
        from samples  s
        join subjects su on su.subject_id = s.subject_id
        where lower(s.condition)   = 'melanoma'
          and lower(s.treatment)   = 'miraclib'
          and lower(s.sample_type) = 'pbmc'
          and s.time_from_treatment_start = 0
        order by s.project_id, s.sample_id
    """
    return pd.read_sql_query(query, conn)


def get_samples_per_project(baseline_df):
    """Part 4-ii-a: number of samples per project."""
    return (
        baseline_df.groupby("project_id")
        .size()
        .reset_index(name="n_samples")
        .sort_values("project_id")
    )


def get_response_counts(baseline_df):
    """Part 4-ii-b: number of unique subjects who are responders/non-responders."""
    return (
        baseline_df.drop_duplicates("subject_id")
        .groupby("response")
        .size()
        .reset_index(name="n_subjects")
    )


def get_sex_counts(baseline_df):
    """Part 4-ii-c: number of unique subjects by sex."""
    return (
        baseline_df.drop_duplicates("subject_id")
        .groupby("sex")
        .size()
        .reset_index(name="n_subjects")
    )


def save_baseline_outputs(baseline_df, proj_df, response_df, sex_df):
    """Save all Part 4 outputs to CSV."""
    import os
    os.makedirs("outputs", exist_ok=True)
    baseline_df.to_csv("outputs/baseline_subset.csv", index=False)
    proj_df.to_csv("outputs/baseline_samples_per_project.csv", index=False)
    response_df.to_csv("outputs/baseline_response_counts.csv", index=False)
    sex_df.to_csv("outputs/baseline_sex_counts.csv", index=False)
    print("Saved outputs/baseline_subset.csv")
    print("Saved outputs/baseline_samples_per_project.csv")
    print("Saved outputs/baseline_response_counts.csv")
    print("Saved outputs/baseline_sex_counts.csv")



## Additional Analysis
def get_time_course(conn):
    """
    Additional analysis: cell population frequencies over time
    for melanoma PBMC patients treated with miraclib,
    split by responder status.
    """
    query = """
        with totals as (
            select sample_id, sum(count) as total_count
            from cell_counts
            group by sample_id
        )
        select
            s.time_from_treatment_start as timepoint,
            su.response,
            cc.population,
            round(100.0 * cc.count / t.total_count, 4) as percentage
        from cell_counts cc
        join totals   t  on t.sample_id   = cc.sample_id
        join samples  s  on s.sample_id   = cc.sample_id
        join subjects su on su.subject_id = s.subject_id
        where lower(s.condition)   = 'melanoma'
          and lower(s.treatment)   = 'miraclib'
          and lower(s.sample_type) = 'pbmc'
          and su.response is not null
        order by timepoint, cc.population
    """
    return pd.read_sql_query(query, conn)