import sqlite3
import pandas as pd

# Create tables with constraints
def create_tables(cursor):
    # Drop tables if they exist to start fresh
    cursor.execute("DROP TABLE IF EXISTS counts")
    cursor.execute("DROP TABLE IF EXISTS samples")
    cursor.execute("DROP TABLE IF EXISTS subjects")
    cursor.execute("DROP TABLE IF EXISTS projects")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        project TEXT PRIMARY KEY
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        subject TEXT PRIMARY KEY,
        project TEXT NOT NULL,
        condition TEXT,
        age INTEGER,
        sex TEXT,
        treatment TEXT,
        response TEXT CHECK (response IN ('yes', 'no') OR response IS NULL),
        FOREIGN KEY (project) REFERENCES projects(project)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS samples (
        sample TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        sample_type TEXT NOT NULL,
        time_from_treatment_start INTEGER,
        FOREIGN KEY (subject) REFERENCES subjects(subject)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS counts (
        sample TEXT NOT NULL,
        population TEXT CHECK (population IN ('b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte')),
        count INTEGER CHECK (count >= 0),
        PRIMARY KEY (sample, population),    
        FOREIGN KEY (sample) REFERENCES samples(sample)
    )
    """)
    print("Tables created")

def load_csv(filepath):
    df = pd.read_csv(filepath)
    print(f"Loaded data from {filepath} with shape {df.shape}")
    return df


def validate_data(df):
    # 1.) Check for required columns
    required_columns = [
        "project", "subject", "condition", "age", "sex",
        "treatment", "response", "sample", "sample_type",
        "time_from_treatment_start", "b_cell", "cd8_t_cell",
        "cd4_t_cell", "nk_cell", "monocyte"
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # 2.) Check for nulls in ID columns
    id_cols = ["project", "subject", "sample"]
    for col in id_cols:
        if df[col].isnull().any():
            raise ValueError(f"Null values found in required column: {col}")
        
    # 3.) Check for duplicate sample IDs
    if df["sample"].duplicated().any():
        raise ValueError("Duplicate sample IDs found")
    
    # 4.) Check for valid cell counts (non-negative integers)
    count_cols = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    if (df[count_cols] < 0).any().any():
        raise ValueError("Negative cell counts found")
    
    print("Data validation passed")
    print(f"- Unique projects: {df['project'].nunique()}")
    print(f"- Unique subjects: {df['subject'].nunique()}")
    print(f"- Unique samples: {df['sample'].nunique()}")

def extract_tables(df):
    # projects table: unique project names
    projects = df[["project"]].drop_duplicates()

    # subjects table: unique subject IDs with their associated project and metadata
    subjects = df[["subject", "project", "condition", "age", "sex", "treatment", "response"]].drop_duplicates()

    # samples table: sample IDs with their associated subject and metadata
    samples = df[["sample", "subject", "sample_type", "time_from_treatment_start"]]

    # counts table: transform from wide to long format: one row per sample + cell population with associated count
    counts = df.melt(
        id_vars=["sample"],
        value_vars=["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"],
        var_name="population",
        value_name="count"
    )
    print(f"Tables extracted")
    return projects, subjects, samples, counts

def insert_data(conn, projects, subjects, samples, counts):
    projects.to_sql("projects", conn, if_exists="append", index=False)
    subjects.to_sql("subjects", conn, if_exists="append", index=False)
    samples.to_sql("samples", conn, if_exists="append", index=False)
    counts.to_sql("counts", conn, if_exists="append", index=False)
    print("Data inserted into database")

def main():
    # Connect to SQLite (creates database if it doesn't exist)
    conn = sqlite3.connect("cell_count.db")
    cursor = conn.cursor()
    # Enforce foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")

    create_tables(cursor)

    df = load_csv("data/cell-count.csv")
    validate_data(df)
    projects, subjects, samples, counts = extract_tables(df)
    insert_data(conn, projects, subjects, samples, counts)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()