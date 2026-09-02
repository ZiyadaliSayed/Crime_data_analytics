from docx import Document
from docx.shared import Pt

doc = Document()
doc.add_heading('Crime Data Analytics Project - Dataset Information', 0)

doc.add_heading('1. Indian Crimes Dataset (Kaggle - 40,000+ rows)', level=2)
doc.add_paragraph('Source Link: https://www.kaggle.com/datasets/sudhanvahg/indian-crimes-dataset (Saved as crime_dataset_india.csv)')
doc.add_paragraph('Usage: This massive 5MB dataset contains over 40,000 incident-level records of crimes committed across major Indian cities from 2020 to 2024. The ETL pipeline filters these incidents for the year 2024, maps the cities to their respective states using the demographics dataset, and aggregates them. Because it is a sample dataset, the totals are mathematically scaled to represent accurate national magnitude for correlative analysis.')
doc.add_paragraph('Columns Used:')
doc.add_paragraph('• City (mapped to State)', style='List Bullet')
doc.add_paragraph('• Date of Occurrence (filtered for 2024)', style='List Bullet')
doc.add_paragraph('• Report Number (used to count Total Crimes)', style='List Bullet')
doc.add_paragraph('• Crime Description (used to filter Murder, Rape, Kidnapping, Robbery, etc.)', style='List Bullet')

doc.add_heading('2. Indian Cities Demographics', level=2)
doc.add_paragraph('Source Link: https://censusindia.gov.in/ (or Open Government Data via Kaggle)')
doc.add_paragraph('Usage: This dataset is used to extract the total urban populations for each state. This population data is mathematically necessary to accurately calculate the true "Crime Rate per 1 Lakh people" rather than just relying on raw, unadjusted crime totals.')
doc.add_paragraph('Columns Used:')
doc.add_paragraph('• state_name', style='List Bullet')
doc.add_paragraph('• population_total (summed by state to calculate Total_Urban_Population)', style='List Bullet')
doc.add_paragraph('• effective_literacy_rate_total (used as a fallback average)', style='List Bullet')

doc.add_heading('3. Wikipedia: Crime in India (Local CSV)', level=2)
doc.add_paragraph('Source Link: https://en.wikipedia.org/wiki/Crime_in_India (Saved as wikipedia_crime_in_india.csv)')
doc.add_paragraph('Usage: The ETL pipeline reads from this local CSV to extract the historical total crime records registered in 2017 for every state. This acts as the pure data baseline for the exact 2017 to 2024 comparisons. Note: Granular breakdowns for specific violent crimes (Murder, Rape, etc.) are not publicly available in this dataset, so the project strictly analyzes "Total Crimes" for the historical comparison.')
doc.add_paragraph('Columns Used:')
doc.add_paragraph('• State/UT', style='List Bullet')
doc.add_paragraph('• 2017 (Historical total crime count)', style='List Bullet')

doc.add_heading('4. Wikipedia: Indian States by Literacy Rate (Local CSV)', level=2)
doc.add_paragraph('Source Link: https://en.wikipedia.org/wiki/List_of_Indian_states_and_union_territories_by_literacy_rate (Saved as wikipedia_literacy_rates.csv)')
doc.add_paragraph('Usage: The pipeline reads this local CSV to extract the official 2017 National Statistical Office (NSO) Survey and the 2023-2024 Periodic Labour Force Survey (PLFS). This provides the exact literacy and illiteracy percentages used to prove the mathematical correlation between illiteracy and crime.')
doc.add_paragraph('Columns Used:')
doc.add_paragraph('• State or UT (Column 0)', style='List Bullet')
doc.add_paragraph('• 2017 Total (Column 4 - NSO Survey)', style='List Bullet')
doc.add_paragraph('• 2024 Total (Column 7 - PLFS Survey)', style='List Bullet')

doc.save('Dataset_Information.docx')
