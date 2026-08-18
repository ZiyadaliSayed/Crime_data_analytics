import sqlite3
import pandas as pd
import os
import glob

def build_warehouse():
    # Database connection
    db_name = 'crime_data_warehouse.db'
    
    # Remove existing db if it exists to start fresh
    if os.path.exists(db_name):
        os.remove(db_name)
        
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Execute DDL schema
    print("Creating schema...")
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    
    # Mapping of dimension tables to their corresponding CSV files
    csv_to_table = {
        'Dim_Time.csv': 'Dim_Time',
        'Dim_Location.csv': 'Dim_Location',
        'Dim_Victim.csv': 'Dim_Victim',
        'Dim_Offender.csv': 'Dim_Offender',
        'Dim_Crime_Profile.csv': 'Dim_Crime_Profile',
    }

    # Primary keys for dimension tables to handle potential duplicates
    pk_map = {
        'Dim_Time': 'Time_ID',
        'Dim_Location': 'Location_ID',
        'Dim_Victim': 'Victim_ID',
        'Dim_Offender': 'Offender_ID',
        'Dim_Crime_Profile': 'Crime_Type_ID'
    }

    print("Loading dimension tables...")
    for csv_file, table_name in csv_to_table.items():
        if os.path.exists(csv_file):
            print(f"Loading {csv_file} into {table_name}...")
            df = pd.read_csv(csv_file)
            if table_name in pk_map:
                df = df.drop_duplicates(subset=[pk_map[table_name]])
            df.to_sql(table_name, conn, if_exists='append', index=False)
        else:
            print(f"Warning: {csv_file} not found.")
            
    print("Loading fact tables...")
    # Load fact tables (handling multiple files if they exist like Fact_Crime_Incidents_2020.csv)
    fact_files = glob.glob('Fact_Crime_Incidents*.csv')
    if not fact_files:
        print("Warning: No Fact_Crime_Incidents CSV files found.")
    
    for fact_file in fact_files:
        print(f"Loading {fact_file} into Fact_Crime_Incidents...")
        df = pd.read_csv(fact_file)
        df.to_sql('Fact_Crime_Incidents', conn, if_exists='append', index=False)
        
    print("Data warehouse build complete!")
    conn.close()

if __name__ == '__main__':
    build_warehouse()
