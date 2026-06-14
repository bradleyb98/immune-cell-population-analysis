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
        cell_population TEXT CHECK (cell_population IN ('b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte')),
        count INTEGER CHECK (count >= 0),
        PRIMARY KEY (sample, cell_population),    
        FOREIGN KEY (sample) REFERENCES samples(sample)
    )
    """)

def load_csv(filepath):
    df = pd.read_csv(filepath)
    return df

def main():
    # Connect to SQLite (creates database if it doesn't exist)
    conn = sqlite3.connect("cell_count.db")
    cursor = conn.cursor()
    create_tables(cursor)
    conn.commit()

    # Enforce foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")

if __name__ == "__main__":
    main()