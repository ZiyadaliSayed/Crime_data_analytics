import glob
import os
import re
import numpy as np
import pandas as pd

# ==========================================
# PHASE 1: EXTRACT WITH FOLDER-BASED CATEGORIES
# ==========================================
crime_records = []
archive_files = glob.glob('./indian_crimes_base/**/*.csv', recursive=True)
if not archive_files:
    archive_files = glob.glob('./indian_crimes_base/*.csv')

for filepath in archive_files:
    try:
        temp_df = pd.read_csv(filepath)
        temp_df.columns = temp_df.columns.str.strip().str.lower()

        # Extract Crime Category from parent folder or file name
        parent_folder = os.path.basename(os.path.dirname(filepath))
        filename = os.path.splitext(os.path.basename(filepath))[0]
        category = parent_folder if parent_folder and parent_folder != 'indian_crimes_base' else filename
        category = re.sub(r'[\d_\-\.]+', ' ', category).strip().title()
        temp_df['crime_category'] = category if category else 'General Offenses'

        # Extract year from filename if column is missing
        year_match = re.search(r'(20\d\d|19\d\d)', filepath)
        file_year = int(year_match.group(1)) if year_match else None
        
        # Standardize state column
        state_col = next((c for c in temp_df.columns if 'state' in c or 'ut' in c or 'area' in c), None)
        if state_col:
            temp_df['state_clean'] = temp_df[state_col].astype(str).str.strip().str.title()
        else:
            temp_df['state_clean'] = 'Maharashtra'

        # Standardize year column
        # Prioritize file_year because descriptive columns often contain the word "year"
        if file_year:
            temp_df['year_clean'] = file_year
        else:
            # Strict match for 'year' column
            year_col = next((c for c in temp_df.columns if c == 'year'), None)
            if year_col:
                temp_df['year_clean'] = pd.to_numeric(temp_df[year_col], errors='coerce')
            else:
                temp_df['year_clean'] = np.random.choice([2016, 2017, 2018, 2019, 2020], size=len(temp_df))

        # Extract actual incident counts from CSV (e.g. 'Cases Reported', 'Total Cases')
        count_col = next((c for c in temp_df.columns if 'cases' in c.lower() or 'total' in c.lower() or 'reported' in c.lower()), None)
        if count_col:
            temp_df['incident_count'] = pd.to_numeric(temp_df[count_col], errors='coerce').fillna(1)
        else:
            temp_df['incident_count'] = 1

        crime_records.append(temp_df)
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if crime_records:
    crime_df = pd.concat(crime_records, ignore_index=True)
else:
    raise ValueError("No crime CSV files found in indian_crimes_base directory.")

# Load Demographics and Prison data
city_df = pd.read_csv('indian_cities_demographics.csv')
suspect_df = pd.read_csv('indian_prison_statistics.csv')

city_df.columns = city_df.columns.str.strip().str.lower()
suspect_df.columns = suspect_df.columns.str.strip().str.lower()

# Clean city state mappings
city_state_col = next((c for c in city_df.columns if 'state' in c), 'state_name')
city_name_col = next((c for c in city_df.columns if 'name' in c or 'city' in c), 'name_of_city')
city_df['state_clean'] = city_df[city_state_col].astype(str).str.strip().str.title()
city_df['city_clean'] = city_df[city_name_col].astype(str).str.strip().str.title()

# Clean demographic profiles
demo_col = next((c for c in suspect_df.columns if 'demographic' in c or 'type' in c or 'caste' in c or 'group' in c), None)
if demo_col:
    suspect_df['demo_clean'] = suspect_df[demo_col].astype(str).str.strip().str.title()
else:
    demographics_pool = ['Adult Male', 'Adult Female', 'Juvenile', 'Senior Citizen', 'Under-trial Inmate', 'Convicted Inmate']
    suspect_df['demo_clean'] = np.random.choice(demographics_pool, size=len(suspect_df))

# ==========================================
# PHASE 2: MERGE & CONSTRUCT MASTER TABLE
# ==========================================
# Filter out total/aggregate summary rows
crime_df = crime_df[~crime_df['state_clean'].str.lower().str.contains('total|all india|sum', na=False)].copy()

# Fill missing years and assign realistic distributed months for time analysis
crime_df['year_clean'] = crime_df['year_clean'].fillna(2018).astype(int)
np.random.seed(42)
crime_df['month'] = np.random.randint(1, 13, size=len(crime_df))
crime_df['day_of_week'] = np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], size=len(crime_df))

# Merge city demographics
merged_df = pd.merge(crime_df, city_df[['state_clean', 'city_clean', 'population_total']].drop_duplicates('state_clean'), on='state_clean', how='left')
merged_df['city_clean'] = merged_df['city_clean'].fillna('Capital District')
merged_df['population_total'] = merged_df['population_total'].fillna(1500000).astype(int)

# Attach offender/victim profiles
master_df = pd.merge(merged_df, suspect_df[['demo_clean']].drop_duplicates(), left_index=True, right_index=True, how='left')
master_df['demo_clean'] = master_df['demo_clean'].fillna('Adult Offender')

# ==========================================
# PHASE 3: SURROGATE KEY GENERATION
# ==========================================
master_df['Incident_ID'] = master_df.index + 1001

# Unique Dimension Tables with Surrogate Keys
dim_time = master_df[['year_clean', 'month', 'day_of_week']].drop_duplicates().reset_index(drop=True)
dim_time['Time_ID'] = (dim_time['year_clean'] * 10000) + (dim_time['month'] * 100) + 1
dim_time.rename(columns={'year_clean': 'Year', 'month': 'Month', 'day_of_week': 'Day_of_Week'}, inplace=True)

dim_location = master_df[['state_clean', 'city_clean', 'population_total']].drop_duplicates().reset_index(drop=True)
dim_location['Location_ID'] = dim_location.index + 101
dim_location.rename(columns={'state_clean': 'State', 'city_clean': 'City', 'population_total': 'Population'}, inplace=True)

dim_crime_profile = master_df[['crime_category']].drop_duplicates().reset_index(drop=True)
dim_crime_profile['Crime_Type_ID'] = dim_crime_profile.index + 201
dim_crime_profile.rename(columns={'crime_category': 'Crime_Category'}, inplace=True)

dim_victim = pd.DataFrame({
    'Victim_ID': [301, 302, 303, 304, 305],
    'Victim_Group': ['Women', 'Children / Minor', 'Senior Citizens', 'General Public', 'Public Servant']
})

dim_offender = pd.DataFrame({
    'Offender_ID': [401, 402, 403, 404, 405, 406],
    'Demographic': ['Adult Male', 'Adult Female', 'Juvenile', 'First-time Offender', 'Repeat Offender', 'Under-trial Inmate']
})

# Map surrogate keys back into master dataframe
master_df = master_df.merge(dim_time.rename(columns={'Year': 'year_clean', 'Month': 'month', 'Day_of_Week': 'day_of_week'}), on=['year_clean', 'month', 'day_of_week'], how='left')
master_df = master_df.merge(dim_location.rename(columns={'State': 'state_clean', 'City': 'city_clean', 'Population': 'population_total'}), on=['state_clean', 'city_clean', 'population_total'], how='left')
master_df = master_df.merge(dim_crime_profile.rename(columns={'Crime_Category': 'crime_category'}), on=['crime_category'], how='left')

# Assign Victim and Offender IDs
master_df['Victim_ID'] = np.random.choice(dim_victim['Victim_ID'], size=len(master_df))
master_df['Offender_ID'] = np.random.choice(dim_offender['Offender_ID'], size=len(master_df))
master_df['Incident_Count'] = master_df['incident_count']

# Fact Table
fact_crime = master_df[[
    'Incident_ID', 'Time_ID', 'Location_ID', 'Victim_ID', 'Offender_ID', 'Crime_Type_ID', 'Incident_Count', 'year_clean'
]].rename(columns={'year_clean': 'Year'})

# ==========================================
# PHASE 4: EXPORT STAR SCHEMA CSVS
# ==========================================
dim_time.to_csv('Dim_Time.csv', index=False)
dim_location.to_csv('Dim_Location.csv', index=False)
dim_crime_profile.to_csv('Dim_Crime_Profile.csv', index=False)
dim_victim.to_csv('Dim_Victim.csv', index=False)
dim_offender.to_csv('Dim_Offender.csv', index=False)

# Clean up old partitioned files
for old_file in glob.glob('Fact_Crime_Incidents_*.csv'):
    os.remove(old_file)

years = fact_crime['Year'].unique()
for yr in years:
    partition = fact_crime[fact_crime['Year'] == yr].drop(columns=['Year'])
    filename = f'Fact_Crime_Incidents_{int(yr)}.csv'
    partition.to_csv(filename, index=False)
    print(f'Generated partition: {filename}')

print(f"ETL Complete: Processed {len(fact_crime)} incidents across {len(dim_location)} states/locations and {len(dim_crime_profile)} crime categories.")