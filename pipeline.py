"""
Runs the full analytical pipeline (Parts 2-4).
Must be run after load_data.py has populated the database.

Run:
    python pipeline.py
"""

import os
import sqlite3

from src.analysis import (
    get_frequency_table,
    save_frequency_table,
    get_responder_comparison,
    run_statistics,
    save_responder_comparison,
    get_baseline_subset,
    get_samples_per_project,
    get_response_counts,
    get_sex_counts,
    save_baseline_outputs,
)
from src.plots import plot_responder_boxplots

db_path = "cell_counts.db"

def main():
    if not os.path.exists(db_path):
        raise FileNotFoundError("cell_counts.db not found. Run `python load_data.py` first.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # part 2: frequency table
    print("\n Part 2: Frequency Table")
    freq_df = get_frequency_table(conn)
    save_frequency_table(freq_df)

    # part 3: responder comparison
    print("\n Part 3: Responder vs Non-Responder")
    resp_df  = get_responder_comparison(conn)
    stats_df = run_statistics(resp_df)
    print(stats_df.to_string(index=False))
    save_responder_comparison(resp_df, stats_df)
    plot_responder_boxplots(resp_df, stats_df)

    # part 4: baseline subset analysis
    print("\n Part 4: Baseline Subset Analysis")
    baseline_df = get_baseline_subset(conn)
    proj_df     = get_samples_per_project(baseline_df)
    response_df = get_response_counts(baseline_df)
    sex_df      = get_sex_counts(baseline_df)

    print(f"Baseline samples: {len(baseline_df)}")
    print("\nSamples per project:")
    print(proj_df.to_string(index=False))
    print("\nResponders/Non-responders:")
    print(response_df.to_string(index=False))
    print("\nMales/Females:")
    print(sex_df.to_string(index=False))

    save_baseline_outputs(baseline_df, proj_df, response_df, sex_df)

    conn.close()
    print("\n Pipeline complete. Outputs written to outputs/")


if __name__ == "__main__":
    main()