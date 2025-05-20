import sqlite3
import pandas as pd
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "datasets.sqlite")

def print_table_schema(conn, table_name):
    print(f"\nSchema for table '{table_name}':")
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    for row in cursor.fetchall():
        print(row)

def print_table_content(conn, table_name):
    print(f"\nContent of table '{table_name}':")
    try:
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        print(df.to_string())
    except pd.io.sql.DatabaseError as e:
        print(f"Could not read table '{table_name}'. Error: {e}")


if __name__ == "__main__":
    if not os.path.exists(db_path):
        print(f"Database file not found at: {db_path}")
        exit()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in the database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Print _metadata content and schema
        if ('_metadata',) in tables:
            print_table_schema(conn, "_metadata")
            print_table_content(conn, "_metadata")
        else:
            print("\n'_metadata' table not found.")

        # Ask user if they want to see content of data tables
        if any(table[0].startswith("data_") for table in tables):
            print("\n--- Data Tables ---")
            for table in tables:
                if table[0].startswith("data_"):
                    print_table_schema(conn, table[0])
                    print_table_content(conn, table[0])
        
    print("\nInspection complete.")
