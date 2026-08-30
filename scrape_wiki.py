import pandas as pd
import sqlite3
import os
import requests

def scrape_real_crime_data():
    url = "https://en.wikipedia.org/wiki/List_of_states_and_union_territories_of_India_by_crime_rate"
    print("Scraping real data from Wikipedia...")
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    
    from io import StringIO
    tables = pd.read_html(StringIO(r.text))
    
    for i, table in enumerate(tables):
        print(f"\nTable {i} Columns: {table.columns.tolist()}")
        if 'State / UT' in table.columns or 'State/UT' in table.columns:
            print(f"-> This table has State/UT!")
            # We can save it to inspect
            table.to_csv(f'wiki_table_{i}.csv', index=False)

if __name__ == '__main__':
    scrape_real_crime_data()
