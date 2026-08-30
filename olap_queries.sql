-- 1. Slice: High Crime States (Total Crimes > 100,000)
SELECT 
    s.State_Name, 
    f.Total_Crimes, 
    f.Crime_Rate
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
WHERE f.Total_Crimes > 100000
ORDER BY f.Total_Crimes DESC;

-- 2. Drill-down: Violent Crimes Breakdown
SELECT 
    s.State_Name, 
    f.Murder, 
    f.Rape, 
    f.Kidnapping, 
    f.Robbery_Dacoity,
    (f.Murder + f.Rape + f.Kidnapping + f.Robbery_Dacoity) AS Total_Violent_Crimes
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
ORDER BY Total_Violent_Crimes DESC
LIMIT 10;

-- 3. Cross-Tabulation: State Socio-Economic vs Crime
SELECT 
    s.State_Name,
    s.Avg_Literacy_Rate,
    f.Crime_Rate,
    p.Illiterate_Prisoners,
    p.Graduate_Prisoners
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
LEFT JOIN Dim_Prison_Stats p ON s.State_ID = p.State_ID
ORDER BY s.Avg_Literacy_Rate DESC;

-- 4. Roll-up: National Aggregation
SELECT 
    SUM(f.Total_Crimes) AS National_Total_Crimes,
    AVG(f.Crime_Rate) AS Avg_National_Crime_Rate,
    SUM(f.Murder) AS National_Total_Murders,
    SUM(p.Total_Prisoners) AS National_Total_Prisoners
FROM Fact_Crime_Stats f
JOIN Dim_State s ON f.State_ID = s.State_ID
LEFT JOIN Dim_Prison_Stats p ON s.State_ID = p.State_ID;
