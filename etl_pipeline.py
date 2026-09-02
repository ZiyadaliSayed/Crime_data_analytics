import pandas as pd
import numpy as np
import requests
from io import StringIO
import os

def clean_state_name(name):
    if pd.isna(name): return name
    name = str(name).strip().title()
    name = name.replace(' (Ut)', '')
    if name == 'Nct Of Delhi' or name == 'Delhi': return 'Delhi'
    if name == 'Jammu And Kashmir': return 'Jammu & Kashmir'
    if name == 'A&N Islands' or name == 'A & N Islands' or name == 'A And N Islands' or name == 'Andaman And Nicobar Islands': return 'Andaman & Nicobar Islands'
    if name == 'D&N Haveli And Daman & Diu' or 'Daman' in name or name == 'Dadra And Nagar Haveli': return 'Dadra & Nagar Haveli and Daman & Diu'
    if name == 'Orissa': return 'Odisha'
    return name

def run_etl():
    print("Starting Multi-Year Real Data ETL Pipeline...")
    
    # 1. Load Local Demographics
    demo_df = pd.read_csv('indian_cities_demographics.csv')
    demo_df['State_Name'] = demo_df['state_name'].apply(clean_state_name)
    state_demo = demo_df.groupby('State_Name').agg(
        Total_Urban_Population=('population_total', 'sum'),
        Avg_Literacy_Rate=('effective_literacy_rate_total', 'mean')
    ).reset_index()

    # 2. (Removed Prison Statistics)    # 3. Load 2023 Crime Data
    crime_df_2023 = pd.read_csv('real_crime_data_scraped.csv')
    crime_df_2023 = crime_df_2023.dropna(subset=['State / UT'])
    crime_df_2023 = crime_df_2023[~crime_df_2023['State / UT'].isin(['India', 'States', 'Union Territories (UT)', 'Union Territories'])]
    crime_df_2023['State_Name'] = crime_df_2023['State / UT'].apply(clean_state_name)
    
    numeric_cols = ['Total Crimes (IPC+SLL) 2023', 'Crime Rate (IPC+SLL) 2023', 'Murder 2023', 'Rape 2023',
                    'Kidnapping 2023', 'Extortion 2023', 'Robbery & Dacoity 2023', 'Hit & Run 2023',
                    'Illegal arms 2023', 'Corruption (Total cases) 2023']
    for col in numeric_cols:
        if col in crime_df_2023.columns:
            crime_df_2023[col] = pd.to_numeric(crime_df_2023[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # 4. Load 2016, 2017, 2018, 2019 Crime Data (From Wikipedia)
    r = requests.get('https://en.wikipedia.org/wiki/Crime_in_India', headers={'User-Agent': 'Mozilla/5.0'})
    historical_table = pd.read_html(StringIO(r.text))[2]
    historical_table = historical_table.dropna(subset=['State/UT'])
    historical_table = historical_table[~historical_table['State/UT'].isin(['India', 'States', 'Union Territories (UT)', 'Total (States)', 'Total (UTs)', 'Total (All India)', 'Union Territories'])]
    historical_table['State_Name'] = historical_table['State/UT'].apply(clean_state_name)
    
    for y in ['2016', '2017', '2018', '2019']:
        historical_table[y] = pd.to_numeric(historical_table[y].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

    # 5. Build Dimensions
    # Scrape real literacy data from Wikipedia
    lit_req = requests.get('https://en.wikipedia.org/wiki/List_of_Indian_states_and_union_territories_by_literacy_rate', headers={'User-Agent': 'Mozilla/5.0'})
    lit_table = pd.read_html(StringIO(lit_req.text))[1]
    
    states = lit_table.iloc[:, 0].astype(str).str.replace(r'\[.*\]', '', regex=True)
    lit_2024 = pd.to_numeric(lit_table.iloc[:, 7], errors='coerce') # 2024 Total
    lit_2017 = pd.to_numeric(lit_table.iloc[:, 4], errors='coerce') # 2017 Total
    lit_2011 = pd.to_numeric(lit_table.iloc[:, 1], errors='coerce') # 2011 Total
    
    lit_2024 = lit_2024.fillna(lit_2017).fillna(lit_2011)
    lit_2017 = lit_2017.fillna(lit_2011).fillna(lit_2024)
    lit_2011 = lit_2011.fillna(lit_2017).fillna(lit_2024)
    
    real_literacy = pd.DataFrame({'State_Name': states, 'Lit_2011': lit_2011, 'Lit_2017': lit_2017, 'Lit_2024': lit_2024})
    real_literacy['State_Name'] = real_literacy['State_Name'].apply(clean_state_name)
    real_literacy = real_literacy.groupby('State_Name').mean().reset_index()
    
    def get_real_literacy(df, year):
        merged = pd.merge(df[['State_Name']], real_literacy, on='State_Name', how='left')
        for c in ['Lit_2011', 'Lit_2017', 'Lit_2024']:
            merged[c] = merged[c].fillna(77.7)
        
        if year == 2017:
            return merged['Lit_2017'].round(2)
        elif year == 2024:
            return merged['Lit_2024'].round(2)
        else:
            return merged['Lit_2024'].round(2)
    
    all_states = pd.concat([crime_df_2023[['State_Name']], historical_table[['State_Name']]]).drop_duplicates()
    dim_state = pd.merge(all_states, state_demo, on='State_Name', how='left')
    dim_state = pd.merge(dim_state, real_literacy[['State_Name', 'Lit_2024']], on='State_Name', how='left')
    
    dim_state['Total_Urban_Population'] = dim_state['Total_Urban_Population'].fillna(0).astype(int)
    dim_state['Avg_Literacy_Rate'] = dim_state['Lit_2024'].fillna(dim_state['Avg_Literacy_Rate'])
    dim_state['Avg_Literacy_Rate'] = dim_state['Avg_Literacy_Rate'].fillna(77.7).round(2)
    dim_state.loc[dim_state['Avg_Literacy_Rate'] == 0, 'Avg_Literacy_Rate'] = 77.7
    dim_state['State_ID'] = range(1, len(dim_state) + 1)
    
    # 6. Build Fact Table - 2024 (Using 2023 crime data as a proxy for 2024 to match literacy survey)
    fact_2024 = pd.merge(dim_state[['State_ID', 'State_Name']], crime_df_2023, on='State_Name', how='inner')
    fact_2024['Year'] = 2024
    fact_2024['Literacy_Rate'] = get_real_literacy(fact_2024, 2024)
    fact_2024 = fact_2024.rename(columns={
        'Total Crimes (IPC+SLL) 2023': 'Total_Crimes',
        'Crime Rate (IPC+SLL) 2023': 'Crime_Rate',
        'Murder 2023': 'Murder', 'Rape 2023': 'Rape', 'Kidnapping 2023': 'Kidnapping',
        'Extortion 2023': 'Extortion', 'Robbery & Dacoity 2023': 'Robbery_Dacoity',
        'Hit & Run 2023': 'Hit_Run', 'Illegal arms 2023': 'Illegal_Arms', 'Corruption (Total cases) 2023': 'Corruption'
    })
    
    rate_cols = ['Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms']
    for col in rate_cols:
        fact_2024[col] = np.where(fact_2024['Crime_Rate'] > 0,
                                   fact_2024[col] * (fact_2024['Total_Crimes'] / fact_2024['Crime_Rate']), 0)
    for col in ['Total_Crimes', 'Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms', 'Corruption']:
        fact_2024[col] = fact_2024[col].round().astype(int)

    # 7. Build Fact Table - 2017 Only
    historical_facts = []
    for year in ['2017']:
        df_y = pd.merge(dim_state[['State_ID', 'State_Name', 'Total_Urban_Population']], historical_table[['State_Name', year]], on='State_Name', how='inner')
        df_y['Year'] = 2017
        df_y['Literacy_Rate'] = get_real_literacy(df_y, 2017)
        df_y = df_y.rename(columns={year: 'Total_Crimes'})
        df_y['Total_Crimes'] = df_y['Total_Crimes'].astype(int)
        df_y['Crime_Rate'] = np.where(df_y['Total_Urban_Population'] > 0, 
                                     (df_y['Total_Crimes'] / df_y['Total_Urban_Population']) * 100000, 0).round(2)
        
        # Calculate specific crimes proportionally based on 2024 ratios (which used the 2023 baseline)
        for col in rate_cols + ['Corruption']:
            ratio_2024 = fact_2024.set_index('State_Name')[col] / fact_2024.set_index('State_Name')['Total_Crimes']
            ratio_2024 = ratio_2024.replace([np.inf, -np.inf], 0).fillna(0)
            
            df_y[col] = (df_y['State_Name'].map(ratio_2024) * df_y['Total_Crimes']).fillna(0).round().astype(int)
            
        historical_facts.append(df_y)
        
    all_facts = [fact_2024] + historical_facts
    fact_crime = pd.concat(all_facts, ignore_index=True)
    
    # 8. Export
    cols_to_keep = ['State_ID', 'Year', 'Total_Crimes', 'Crime_Rate', 'Literacy_Rate', 'Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms', 'Corruption']
    fact_crime = fact_crime[cols_to_keep]

    dim_state[['State_ID', 'State_Name', 'Total_Urban_Population', 'Avg_Literacy_Rate']].to_csv('Dim_State.csv', index=False)
    fact_crime.to_csv('Fact_Crime_Stats.csv', index=False)

    print("Multi-Year ETL Pipeline completed. Data exported to CSVs.")

if __name__ == "__main__":
    run_etl()