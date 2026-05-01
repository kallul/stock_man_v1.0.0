import pandas as pd
import sqlite3
import os

from config import DB_PATH

def ingest_csv(csv_path: str):
    print(f"Ingesting CSV from {csv_path} into SQLite at {DB_PATH}...")
    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
    except UnicodeDecodeError:
        print("UTF-8 decoding failed, falling back to cp1252 encoding...")
        df = pd.read_csv(csv_path, encoding='cp1252')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df.to_sql("stocks", conn, if_exists="replace", index=False)
        row_count = len(df)
        columns = df.columns.tolist()
        return row_count, columns
    except Exception as e:
        print(f"Error ingesting CSV: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        csv_to_ingest = sys.argv[1]
        ingest_csv(csv_to_ingest)
    else:
        print("Usage: python -m ingest.csv_ingestor <csv_path>")
