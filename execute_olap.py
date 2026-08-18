import sqlite3
import pandas as pd
import os

def execute_olap_queries():
    db_name = 'crime_data_warehouse.db'
    if not os.path.exists(db_name):
        print(f"Error: Database {db_name} not found. Please run build_warehouse.py first.")
        return

    conn = sqlite3.connect(db_name)
    
    with open('olap_queries.sql', 'r') as f:
        sql_content = f.read()
        
    # Split queries by the "-- X." prefix that starts a new query block
    if sql_content.startswith('-- '):
        sql_content = '\n' + sql_content
        
    query_blocks = sql_content.split('\n-- ')
    
    for block in query_blocks:
        block = block.strip()
        if not block:
            continue
            
        lines = block.split('\n')
        # The first line is the title (e.g., "1. Roll-up: ...")
        title = lines[0]
        
        # The rest is potentially comments and then the query
        query_lines = []
        for line in lines[1:]:
            if not line.strip().startswith('--'):
                query_lines.append(line)
                
        query = '\n'.join(query_lines).strip()
        
        if query:
            print(f"\n{'-'*80}")
            print(f"Executing: {title}")
            print(f"{'-'*80}")
            try:
                # Read into pandas DataFrame
                df = pd.read_sql_query(query, conn)
                if df.empty:
                    print("Result: No data returned.\n")
                else:
                    # Print formatted table using pandas to_string
                    print(df.to_string(index=False))
                    print(f"\nTotal rows returned: {len(df)}")
            except Exception as e:
                print(f"Error executing query:\n{query}\nException: {e}")
                
    conn.close()

if __name__ == '__main__':
    execute_olap_queries()
