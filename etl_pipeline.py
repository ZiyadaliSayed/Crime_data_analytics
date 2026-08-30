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

    # 2. Load Local Prison Statistics
    prison_df = pd.read_csv('indian_prison_statistics.csv')
    prison_df['State_Name'] = prison_df['State/UT'].apply(clean_state_name)
    state_prison = prison_df.groupby('State_Name').agg(
        Total_Prisoners=('Total - Total', 'sum'),
        Illiterate_Prisoners=('Educational Standard - Illiterate', 'sum'),
        Graduate_Prisoners=('Educational Standard - Graduate', 'sum')
    ).reset_index()

    # 3. Load 2023 Crime Data
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
    all_states = pd.concat([crime_df_2023[['State_Name']], historical_table[['State_Name']]]).drop_duplicates()
    dim_state = pd.merge(all_states, state_demo, on='State_Name', how='left')
    dim_state['Total_Urban_Population'] = dim_state['Total_Urban_Population'].fillna(0).astype(int)
    dim_state['Avg_Literacy_Rate'] = dim_state['Avg_Literacy_Rate'].fillna(77.7).round(2)
    dim_state.loc[dim_state['Avg_Literacy_Rate'] == 0, 'Avg_Literacy_Rate'] = 77.7
    dim_state['State_ID'] = range(1, len(dim_state) + 1)
    
    dim_prison = pd.merge(dim_state[['State_ID', 'State_Name']], state_prison, on='State_Name', how='left')
    dim_prison = dim_prison.fillna(0)
    for col in ['Total_Prisoners', 'Illiterate_Prisoners', 'Graduate_Prisoners']:
        dim_prison[col] = dim_prison[col].astype(int)
    dim_prison['Prison_Stat_ID'] = range(1, len(dim_prison) + 1)

    # 6. Build Fact Table - 2023
    fact_2023 = pd.merge(dim_state[['State_ID', 'State_Name']], crime_df_2023, on='State_Name', how='inner')
    fact_2023['Year'] = 2023
    fact_2023 = fact_2023.rename(columns={
        'Total Crimes (IPC+SLL) 2023': 'Total_Crimes',
        'Crime Rate (IPC+SLL) 2023': 'Crime_Rate',
        'Murder 2023': 'Murder', 'Rape 2023': 'Rape', 'Kidnapping 2023': 'Kidnapping',
        'Extortion 2023': 'Extortion', 'Robbery & Dacoity 2023': 'Robbery_Dacoity',
        'Hit & Run 2023': 'Hit_Run', 'Illegal arms 2023': 'Illegal_Arms', 'Corruption (Total cases) 2023': 'Corruption'
    })
    
    rate_cols = ['Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms']
    for col in rate_cols:
        fact_2023[col] = np.where(fact_2023['Crime_Rate'] > 0,
                                   fact_2023[col] * (fact_2023['Total_Crimes'] / fact_2023['Crime_Rate']), 0)
    for col in ['Total_Crimes', 'Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms', 'Corruption']:
        fact_2023[col] = fact_2023[col].round().astype(int)

    # 7. Build Fact Table - 2016 to 2019
    historical_facts = []
    for year in ['2016', '2017', '2018', '2019']:
        df_y = pd.merge(dim_state[['State_ID', 'State_Name', 'Total_Urban_Population']], historical_table[['State_Name', year]], on='State_Name', how='inner')
        df_y['Year'] = int(year)
        df_y = df_y.rename(columns={year: 'Total_Crimes'})
        df_y['Total_Crimes'] = df_y['Total_Crimes'].astype(int)
        df_y['Crime_Rate'] = np.where(df_y['Total_Urban_Population'] > 0, 
                                     (df_y['Total_Crimes'] / df_y['Total_Urban_Population']) * 100000, 0).round(2)
        
        # Calculate specific crimes proportionally based on 2023 ratios
        for col in rate_cols + ['Corruption']:
            # Get 2023 ratio for this state: (Crime / Total_Crimes)
            ratio_2023 = fact_2023.set_index('State_Name')[col] / fact_2023.set_index('State_Name')['Total_Crimes']
            ratio_2023 = ratio_2023.replace([np.inf, -np.inf], 0).fillna(0)
            
            df_y[col] = (df_y['State_Name'].map(ratio_2023) * df_y['Total_Crimes']).fillna(0).round().astype(int)
            
        historical_facts.append(df_y)
        
    # 7.5 Mathematically Interpolate Missing Datasets (2020, 2021, 2022)
    # Since direct raw CSVs are behind captchas/logins, we interpolate state-wise between 2019 and 2023.
    interpolated_facts = []
    df_2019 = historical_facts[-1].groupby('State_Name').sum(numeric_only=True)
    df_2023 = fact_2023.groupby('State_Name').sum(numeric_only=True)
    
    for year in [2020, 2021, 2022]:
        weight_2023 = (year - 2019) / (2023 - 2019)
        weight_2019 = 1 - weight_2023
        
        df_interp = pd.DataFrame(index=df_2023.index)
        # Handle states that might only exist in one of the tables gracefully
        common_states = df_2019.index.intersection(df_2023.index)
        
        df_interp['Total_Crimes'] = 0
        df_interp.loc[common_states, 'Total_Crimes'] = (df_2019.loc[common_states, 'Total_Crimes'] * weight_2019 + 
                                                        df_2023.loc[common_states, 'Total_Crimes'] * weight_2023).round().astype(int)
                                                        
        # For states like Ladakh that were created after 2019 and thus missing from 2019 dataset, backfill with 2023 data
        missing_states = df_2023.index.difference(df_2019.index)
        if len(missing_states) > 0:
            df_interp.loc[missing_states, 'Total_Crimes'] = df_2023.loc[missing_states, 'Total_Crimes']
            
        df_interp['Year'] = year
        df_interp = df_interp.reset_index()
        
        df_y = pd.merge(dim_state[['State_ID', 'State_Name', 'Total_Urban_Population']], df_interp, on='State_Name', how='inner')
        df_y['Crime_Rate'] = np.where(df_y['Total_Urban_Population'] > 0, 
                                     (df_y['Total_Crimes'] / df_y['Total_Urban_Population']) * 100000, 0).round(2)
                                     
        for col in rate_cols + ['Corruption']:
            ratio_2023 = fact_2023.set_index('State_Name')[col] / fact_2023.set_index('State_Name')['Total_Crimes']
            ratio_2023 = ratio_2023.replace([np.inf, -np.inf], 0).fillna(0)
            df_y[col] = (df_y['State_Name'].map(ratio_2023) * df_y['Total_Crimes']).fillna(0).round().astype(int)
            
        interpolated_facts.append(df_y)
        
    all_facts = [fact_2023] + historical_facts + interpolated_facts
    fact_crime = pd.concat(all_facts, ignore_index=True)
    
    # 8. Export
    cols_to_keep = ['State_ID', 'Year', 'Total_Crimes', 'Crime_Rate', 'Murder', 'Rape', 'Kidnapping', 'Extortion', 'Robbery_Dacoity', 'Hit_Run', 'Illegal_Arms', 'Corruption']
    fact_crime = fact_crime[cols_to_keep]

    dim_state[['State_ID', 'State_Name', 'Total_Urban_Population', 'Avg_Literacy_Rate']].to_csv('Dim_State.csv', index=False)
    dim_prison[['Prison_Stat_ID', 'State_ID', 'Total_Prisoners', 'Illiterate_Prisoners', 'Graduate_Prisoners']].to_csv('Dim_Prison_Stats.csv', index=False)
    fact_crime.to_csv('Fact_Crime_Stats.csv', index=False)

    print("Multi-Year ETL Pipeline completed. Data exported to CSVs.")

if __name__ == "__main__":
    run_etl()