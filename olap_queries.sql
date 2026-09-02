-- 1. Slice: High Crime States in 2024 (Isolating a single dimension: Year=2024, Total_Crimes > 100,000)
SELECT 
    s.State_Name, 
    f.Total_Crimes, 
    f.Crime_Rate
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year = 2024 AND f.Total_Crimes > 100000
ORDER BY f.Total_Crimes DESC
LIMIT 10;

-- 2. Dice: Specific Violent Crimes in Top States (Subsetting Year and Location)
SELECT 
    s.State_Name, 
    f.Year,
    f.Murder, 
    f.Rape
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year IN (2017, 2024) AND s.State_Name IN ('Uttar Pradesh', 'Maharashtra', 'Madhya Pradesh', 'Kerala')
ORDER BY s.State_Name, f.Year;

-- 3. Roll-up: National Aggregation of Crimes by Year (Summarizing data up the hierarchy)
SELECT 
    f.Year, 
    SUM(f.Total_Crimes) AS National_Total_Crimes,
    ROUND(AVG(f.Crime_Rate), 2) AS Avg_National_Crime_Rate,
    SUM(f.Murder) AS National_Total_Murders
FROM Fact_Crime_Stats f
GROUP BY f.Year
ORDER BY f.Year DESC;

-- 4. Drill-down: Violent Crimes Breakdown for 2024 (Navigating from total crimes down to specific categories)
SELECT 
    s.State_Name, 
    f.Murder, 
    f.Rape, 
    f.Kidnapping, 
    f.Robbery,
    (f.Murder + f.Rape + f.Kidnapping + f.Robbery) AS Total_Violent_Crimes
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year = 2024
ORDER BY Total_Violent_Crimes DESC
LIMIT 10;

-- 5. Pivot (Cross-tabulation): States vs Years for Total Crimes (Rotating the data cube)
SELECT 
    s.State_Name,
    MAX(CASE WHEN f.Year = 2017 THEN f.Total_Crimes ELSE 0 END) AS Crimes_2017,
    MAX(CASE WHEN f.Year = 2024 THEN f.Total_Crimes ELSE 0 END) AS Crimes_2024,
    (MAX(CASE WHEN f.Year = 2024 THEN f.Total_Crimes ELSE 0 END) - 
     MAX(CASE WHEN f.Year = 2017 THEN f.Total_Crimes ELSE 0 END)) AS Growth_2017_to_2024
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
GROUP BY s.State_Name
ORDER BY Crimes_2024 DESC
LIMIT 10;

-- 6. Slice: Low Literacy States and Crime Rates (Isolating dimension where Literacy < 75%)
SELECT 
    s.State_Name,
    s.Avg_Literacy_Rate,
    f.Crime_Rate,
    f.Total_Crimes
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year = 2024 AND s.Avg_Literacy_Rate < 75
ORDER BY f.Crime_Rate DESC;

-- 7. Dice: Property Crimes in South Indian States (Subsetting Location and Crime Type)
SELECT 
    s.State_Name,
    f.Robbery
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year = 2024 AND s.State_Name IN ('Kerala', 'Tamil Nadu', 'Karnataka', 'Andhra Pradesh', 'Telangana')
ORDER BY f.Robbery DESC;

-- 8. Top-N Analysis: Highest Murder Rates per 1 Lakh Population (Advanced Aggregation)
SELECT 
    s.State_Name,
    f.Murder,
    s.Total_Urban_Population,
    ROUND((CAST(f.Murder AS FLOAT) / s.Total_Urban_Population) * 100000, 2) AS Murders_Per_1_Lakh
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Year = 2024 AND s.Total_Urban_Population > 1000000
ORDER BY Murders_Per_1_Lakh DESC
LIMIT 5;
