import os
import shutil
import psycopg2
import pandas as pd
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
PARENT_DIR = os.path.dirname(SCRIPT_DIR)  # One folder up from the script

# Define the relative paths for incoming and archived data in the parent directory
ARCHIVE_DIR = os.path.join(PARENT_DIR, 'archived-data')
INCOMING_DIR = os.path.join(PARENT_DIR, 'incoming-data')

DB_CONFIG = {
    'dbname': 'eltdb',
    'user': 'eltuser',
    'password': 'eltpassword',
    'host': 'postgres-elt',
    'port': 5432
}

TARGET_TABLE = 'staging_raw_data'

def process_csv(file_path):
    df = pd.read_csv(file_path)
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create table if it does not exist
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS "{TARGET_TABLE}" (
        Customer_ID VARCHAR(255),
        Age INT,
        Gender VARCHAR(50),
        Tenure INT,
        Monthly_Charges DECIMAL,
        Contract_Type VARCHAR(50),
        Internet_Service VARCHAR(50),
        Total_Charges DECIMAL,
        Tech_Support VARCHAR(50),
        Churn VARCHAR(50),
        processed_at TIMESTAMP
    );
    """

    cursor.execute(create_table_query)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_staging_raw_data_processed_at
        ON staging_raw_data (processed_at);
    """)

    for _, row in df.iterrows():
        cursor.execute(
            f"""INSERT INTO {TARGET_TABLE} 
            (Customer_ID, Age, Gender, Tenure, Monthly_Charges, Contract_Type, 
                                Internet_Service, Total_Charges, Tech_Support, Churn, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL)""",
            tuple(row)
        )

    conn.commit()
    cursor.close()
    conn.close()

def run_ingestion():
    for filename in os.listdir(INCOMING_DIR):
        if filename.endswith('.csv'):
            full_path = os.path.join(INCOMING_DIR, filename)
            print(f"Processing: {full_path}")
            process_csv(full_path)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_path = os.path.join(ARCHIVE_DIR, f"{filename}")
            shutil.move(full_path, archived_path)
            print(f"Archived: {archived_path}")

if __name__ == '__main__':
    run_ingestion()
