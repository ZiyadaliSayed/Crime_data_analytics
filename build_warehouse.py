import sqlite3
import pandas as pd
import os

def build_warehouse():
    db_name = 'crime_data_warehouse.db'
    
    if os.path.exists(db_name):
        os.remove(db_name)
        
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("Creating schema...")
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    
    csv_to_table = {
        'Dim_State.csv': 'Dim_State',
        'Dim_Prison_Stats.csv': 'Dim_Prison_Stats',
        'Fact_Crime_Stats.csv': 'Fact_Crime_Stats'
    }

    print("Loading data into warehouse...")
    for csv_file, table_name in csv_to_table.items():
        if os.path.exists(csv_file):
            print(f"Loading {csv_file} into {table_name}...")
            df = pd.read_csv(csv_file)
            df.to_sql(table_name, conn, if_exists='append', index=False)
        else:
            print(f"Error: {csv_file} not found. Please run etl_pipeline.py first.")
            
    print("Data warehouse build complete!")
    conn.close()

if __name__ == '__main__':
    build_warehouse()
