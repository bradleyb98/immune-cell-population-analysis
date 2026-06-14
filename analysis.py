import sqlite3
import pandas as pd

def calculate_frequencies(cursor):
    cursor.execute("""
    SELECT
        s.sample,
        s.subject,
        b.condition,
        b.treatment,
        b.response,
        s.sample_type,
        s.time_from_treatment_start,
        c.population,
        c.count,
        SUM(c.count) OVER (PARTITION BY s.sample) AS total_count,
        ROUND(100.0 * c.count / SUM(c.count) OVER (PARTITION BY s.sample), 2) AS percentage
    FROM counts c
    JOIN samples s ON c.sample = s.sample
    JOIN subjects b ON s.subject = b.subject             
    """)

def main():
    # Connect to database
    conn = sqlite3.connect("cell_count.db")
    cursor = conn.cursor()


if __name__ == "__main__":
    main()