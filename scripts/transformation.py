import psycopg2
import pandas as pd
import hashlib
from datetime import datetime

DB_CONFIG = {
    'dbname': 'eltdb',
    'user': 'eltuser',
    'password': 'eltpassword',
    'host': 'postgres-elt',
    'port': 5432
}

def hash_customer_id(customer_id):
    return hashlib.sha256(customer_id.encode('utf-8')).hexdigest()

def transform_row(row):
    return {
        'customer_hash': hash_customer_id(str(row['customer_id'])),
        'age': row['age'] if pd.notnull(row['age']) else 0,
        'gender': row['gender'] if pd.notnull(row['gender']) else 'Male',
        'tenure': row['tenure'] if pd.notnull(row['tenure']) else 0,
        'monthly_charges': row['monthly_charges'] if pd.notnull(row['monthly_charges']) else 0.0,
        'contract_type': row['contract_type'] if pd.notnull(row['contract_type']) else  row['monthly_charges']*row['tenure'],
        'internet_service': row['internet_service'] if row['internet_service'] != 'NaN' else 'None',
        'total_charges': row['total_charges'] if pd.notnull(row['total_charges']) else 0.0,
        'tech_support': row['tech_support'] if pd.notnull(row['tech_support']) else 'No',
        'churn': row['churn'] if pd.notnull(row['churn']) else 'No',
    }

def create_final_table_if_not_exists(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS final_processed_data (
            customer_hash VARCHAR(255),
            age INT,
            gender VARCHAR(50),
            tenure INT,
            monthly_charges DECIMAL(7, 2),
            contract_type VARCHAR(50),
            internet_service VARCHAR(50),
            total_charges DECIMAL(7, 2),
            tech_support VARCHAR(50),
            churn VARCHAR(50)
        );
    """)

def process_and_migrate():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    create_final_table_if_not_exists(cursor)

    # Read from staging
    cursor.execute("SELECT * FROM staging_raw_data WHERE processed_at IS NULL")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    print(columns)

    df = pd.DataFrame(rows, columns=columns)

    for _, row in df.iterrows():
        transformed = transform_row(row)
        cursor.execute("""
            INSERT INTO final_processed_data (
                customer_hash, age, gender, tenure, monthly_charges, 
                contract_type, internet_service, total_charges, tech_support, churn
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, tuple(transformed.values()))

        # Mark this row as processed
        cursor.execute("""
            UPDATE staging_raw_data 
            SET processed_at = %s 
            WHERE customer_id = %s
        """, (datetime.now(), row['customer_id']))

    conn.commit()
    cursor.close()
    conn.close()
    print("Data transformed and migrated successfully.")

if __name__ == '__main__':
    process_and_migrate()
