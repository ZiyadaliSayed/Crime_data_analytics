import glob
import numpy as np
import pandas as pd

# ==========================================
# PHASE 1: EXTRACT (Load All Raw Datasets)
# ==========================================
crime_files = glob.glob('./indian_crimes_base/**/*.csv', recursive=True)
if not crime_files:
    crime_files = glob.glob('./indian_crimes_base/*.csv')

crime_df = pd.concat([pd.read_csv(f) for f in crime_files], ignore_index=True)
city_df = pd.read_csv('indian_cities_demographics.csv')
suspect_df = pd.read_csv('indian_prison_statistics.csv')

# Standardize column headers
crime_df.columns = crime_df.columns.str.strip().str.lower()
city_df.columns = city_df.columns.str.strip().str.lower()
suspect_df.columns = suspect_df.columns.str.strip().str.lower()

if 'state/ut' in crime_df.columns:
    crime_df.rename(columns={'state/ut': 'state_name'}, inplace=True)
if 'name_of_city' in city_df.columns:
    city_df.rename(columns={'name_of_city': 'city'}, inplace=True)

# ==========================================
# PHASE 2: MERGE DATASETS
# ==========================================
if 'city' in crime_df.columns and 'city' in city_df.columns:
    crime_df['city'] = crime_df['city'].astype(str).str.title()
    city_df['city'] = city_df['city'].astype(str).str.title()
    merged_df = pd.merge(crime_df, city_df, on='city', how='left')
else:
    merged_df = pd.merge(
        crime_df, city_df, left_index=True, right_index=True, how='left'
    )

master_df = pd.merge(
    merged_df, suspect_df, left_index=True, right_index=True, how='left'
)

# ==========================================
# PHASE 3: TRANSFORM & ENGINEER KEYS
# ==========================================
master_df['Incident_ID'] = master_df.index + 1001

if 'year' in master_df.columns:
    master_df['Year'] = (
        pd.to_numeric(master_df['year'], errors='coerce')
        .fillna(2020)
        .astype(int)
    )
else:
    master_df['Year'] = 2020

master_df['Time_ID'] = master_df['Year'].astype(str) + '0101'
master_df['Location_ID'] = (master_df.index % 50) + 1
master_df['Crime_Type_ID'] = (master_df.index % 20) + 1
master_df['Victim_ID'] = master_df.index + 5000
master_df['Offender_ID'] = master_df.index + 9000
master_df['Incident_Count'] = 1

# ==========================================
# PHASE 4: EXTRACT STAR SCHEMA TABLES
# ==========================================
dim_time = pd.DataFrame(
    {
        'Time_ID': master_df['Time_ID'],
        'Year': master_df['Year'],
        'Month': 1,
        'Day_of_Week': 'Monday',
    }
).drop_duplicates()

dim_location = pd.DataFrame(
    {
        'Location_ID': master_df['Location_ID'],
        'State': master_df.get('state_name', 'Unknown'),
        'City': master_df.get('city', 'Unknown'),
        'Population': master_df.get('population_total', 0),
    }
).drop_duplicates()

dim_victim = pd.DataFrame(
    {
        'Victim_ID': master_df['Victim_ID'],
        'Victim_Group': master_df.get('group_name', 'General'),
    }
).drop_duplicates()

dim_offender = pd.DataFrame(
    {
        'Offender_ID': master_df['Offender_ID'],
        'Demographic': master_df.get('demographic', 'Unknown'),
    }
).drop_duplicates()

dim_crime_profile = pd.DataFrame(
    {
        'Crime_Type_ID': master_df['Crime_Type_ID'],
        'Crime_Category': master_df.get('crime_head', 'General'),
    }
).drop_duplicates()

fact_crime = pd.DataFrame(
    {
        'Incident_ID': master_df['Incident_ID'],
        'Time_ID': master_df['Time_ID'],
        'Location_ID': master_df['Location_ID'],
        'Victim_ID': master_df['Victim_ID'],
        'Offender_ID': master_df['Offender_ID'],
        'Crime_Type_ID': master_df['Crime_Type_ID'],
        'Incident_Count': master_df['Incident_Count'],
        'Year': master_df['Year'],
    }
)

# ==========================================
# PHASE 5: EXPORT DIMENSIONS & PARTITION FACT
# ==========================================
dim_time.to_csv('Dim_Time.csv', index=False)
dim_location.to_csv('Dim_Location.csv', index=False)
dim_victim.to_csv('Dim_Victim.csv', index=False)
dim_offender.to_csv('Dim_Offender.csv', index=False)
dim_crime_profile.to_csv('Dim_Crime_Profile.csv', index=False)

years = fact_crime['Year'].dropna().unique()
for yr in years:
    partition = fact_crime[fact_crime['Year'] == yr].drop(columns=['Year'])
    filename = f'Fact_Crime_Incidents_{int(yr)}.csv'
    partition.to_csv(filename, index=False)
    print(f'Generated partition: {filename}')

print('ETL Execution Complete. Star schema generated successfully.')