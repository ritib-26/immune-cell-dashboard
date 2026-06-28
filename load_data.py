"""
Part 1: Initialize and load 

Run:
    python load_data.py
"""

import sqlite3
import csv
import os
import sys

db_path  = os.path.join(os.path.dirname(__file__), "cell_counts.db")
csv_path = os.path.join(os.path.dirname(__file__), "cell-count.csv")

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    project_id   TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id   TEXT PRIMARY KEY,
    age          INTEGER,
    sex          TEXT,
    response     TEXT
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT REFERENCES subjects(subject_id),
    project_id                 TEXT REFERENCES projects(project_id),
    condition                  TEXT,
    treatment                  TEXT,
    sample_type                TEXT,
    time_from_treatment_start  REAL
);

CREATE TABLE IF NOT EXISTS cell_counts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id    TEXT NOT NULL REFERENCES samples(sample_id),
    population   TEXT NOT NULL,
    count        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cell_counts_sample ON cell_counts(sample_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_pop    ON cell_counts(population);
CREATE INDEX IF NOT EXISTS idx_samples_subject    ON samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_samples_treatment  ON samples(treatment);
"""

populations = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def init_db(conn):
    # run all the create table and create index statements at once
    conn.executescript(SCHEMA)
    # clear cell_counts before loading to prevent duplicates on re-runs
    conn.execute("delete from cell_counts")
    conn.commit() # save the changes to the database
    print("Schema initialised!")

def load_csv(conn, csv_path):
    # exit early if the file doesn't exist
    if not os.path.exists(csv_path):
        sys.exit(f"ERROR: {csv_path} not found.")

    # track which projects/subjects we've already inserted to avoid duplicates
    projects_seen = set()
    subjects_seen = set()

    # accumulate rows in memory before bulk inserting into the database
    sample_rows = []
    count_rows  = []

    # open the csv file
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)  # reads each row as a dictionary keyed by column name

        for row in reader:
            project_id = row["project"]
            subject_id = row["subject"]
            sample_id  = row["sample"]

            # insert project if we haven't seen it yet
            if project_id not in projects_seen:
                conn.execute(
                    "insert or ignore into projects (project_id) values (?)",
                    (project_id,)
                )
                projects_seen.add(project_id)

            # insert subject if we haven't seen it yet
            if subject_id not in subjects_seen:
                conn.execute(
                    "insert or ignore into subjects (subject_id, age, sex, response) values (?,?,?,?)",
                    (
                        subject_id,
                        int(row["age"]) if row["age"] else None,  # convert to int, or None if empty
                        row["sex"] or None,
                        row["response"] or None,
                    )
                )
                subjects_seen.add(subject_id)

            # collect sample metadata as a tuple for bulk insert later
            sample_rows.append((
                sample_id,
                subject_id,
                project_id,
                row["condition"] or None,
                row["treatment"] or None,
                row["sample_type"] or None,
                float(row["time_from_treatment_start"]) if row["time_from_treatment_start"] else None,
            ))

            # collect one row per cell population for this sample
            for pop in populations:
                if row.get(pop):
                    count_rows.append((sample_id, pop, int(float(row[pop]))))

    # bulk insert all samples at once 
    conn.executemany(
        """insert or replace into samples
           (sample_id, subject_id, project_id, condition, treatment, sample_type, time_from_treatment_start)
           values (?,?,?,?,?,?,?)""",
        sample_rows,
    )

    # bulk insert all cell counts at once
    conn.executemany(
        "insert into cell_counts (sample_id, population, count) values (?,?,?)",
        count_rows,
    )

    # save everything to the database
    conn.commit()
    print(f"Loaded {len(sample_rows)} samples, {len(count_rows)} cell-count rows.")

def main():
    print(f"Database --> {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    load_csv(conn, csv_path)
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()

