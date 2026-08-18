import os
import pandas as pd
import numpy as np

states = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu & Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "A & N Islands", "Chandigarh", "D&N Haveli", "Daman & Diu",
    "Delhi Ut", "Lakshadweep", "Puducherry"
]

crimes = ["Murder", "Theft", "Cyber Crime", "Kidnapping"]
years = [2016, 2017, 2018]
base_dir = "indian_crimes_base"

np.random.seed(42)

for crime in crimes:
    crime_dir = os.path.join(base_dir, crime)
    os.makedirs(crime_dir, exist_ok=True)
    
    for year in years:
        file_path = os.path.join(crime_dir, f"{year} {crime}.csv")
        
        # Generating random reported cases to make the data look realistic
        df = pd.DataFrame({
            "S. No": range(1, len(states) + 1),
            "State/UT": states,
            "Cases Reported": np.random.randint(10, 5000, size=len(states)),
            "Arrests Made": np.random.randint(5, 4000, size=len(states))
        })
        
        df.to_csv(file_path, index=False)
        print(f"Generated: {file_path}")
