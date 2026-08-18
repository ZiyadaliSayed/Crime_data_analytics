-- 1. Roll-up: Aggregating from City to State level
SELECT 
    l.State,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Location l ON f.Location_ID = l.Location_ID
GROUP BY l.State
ORDER BY Total_Incidents DESC;

-- 2. Roll-up: Aggregating from Month to Year level
SELECT 
    t.Year,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
GROUP BY t.Year
ORDER BY t.Year;

-- 3. Drill-down: Deconstructing annual crime trends into monthly breakdowns
SELECT 
    t.Year,
    t.Month,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
GROUP BY t.Year, t.Month
ORDER BY t.Year, t.Month;

-- 4. Drill-down: Deconstructing annual trends into monthly breakdowns by Crime Category
SELECT 
    t.Year,
    t.Month,
    c.Crime_Category,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
JOIN Dim_Crime_Profile c ON f.Crime_Type_ID = c.Crime_Type_ID
GROUP BY t.Year, t.Month, c.Crime_Category
ORDER BY t.Year, t.Month, Total_Incidents DESC;

-- 5. Slice: Filtering by a single dimension (Specific State)
SELECT 
    l.City,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Location l ON f.Location_ID = l.Location_ID
WHERE l.State = (SELECT MIN(State) FROM Dim_Location)
GROUP BY l.City
ORDER BY Total_Incidents DESC
LIMIT 10;

-- 6. Slice: Filtering by a single dimension (Specific Crime Category)
SELECT 
    l.State,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Location l ON f.Location_ID = l.Location_ID
JOIN Dim_Crime_Profile c ON f.Crime_Type_ID = c.Crime_Type_ID
WHERE c.Crime_Category = (SELECT MIN(Crime_Category) FROM Dim_Crime_Profile)
GROUP BY l.State
ORDER BY Total_Incidents DESC;

-- 7. Dice: Multi-dimensional filtering by Year, State, and Victim Group
SELECT 
    t.Year,
    l.State,
    v.Victim_Group,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
JOIN Dim_Location l ON f.Location_ID = l.Location_ID
JOIN Dim_Victim v ON f.Victim_ID = v.Victim_ID
WHERE 
    t.Year = (SELECT MAX(Year) FROM Dim_Time)
    AND l.State = (SELECT MIN(State) FROM Dim_Location)
    AND v.Victim_Group = (SELECT MIN(Victim_Group) FROM Dim_Victim)
GROUP BY t.Year, l.State, v.Victim_Group;

-- 8. Dice: Multi-dimensional filtering by Month, City, and Offender Demographic
SELECT 
    t.Month,
    l.City,
    o.Demographic,
    SUM(f.Incident_Count) AS Total_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
JOIN Dim_Location l ON f.Location_ID = l.Location_ID
JOIN Dim_Offender o ON f.Offender_ID = o.Offender_ID
WHERE 
    t.Month = (SELECT MIN(Month) FROM Dim_Time)
    AND l.City = (SELECT MAX(City) FROM Dim_Location)
    AND o.Demographic = (SELECT MIN(Demographic) FROM Dim_Offender)
GROUP BY t.Month, l.City, o.Demographic;

-- 9. Pivot / Cross-tabulation: Matrix of Crime Categories across Years
SELECT 
    c.Crime_Category,
    SUM(CASE WHEN t.Year = 2020 THEN f.Incident_Count ELSE 0 END) AS Incidents_2020,
    SUM(CASE WHEN t.Year = 2021 THEN f.Incident_Count ELSE 0 END) AS Incidents_2021,
    SUM(CASE WHEN t.Year = 2022 THEN f.Incident_Count ELSE 0 END) AS Incidents_2022
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
JOIN Dim_Crime_Profile c ON f.Crime_Type_ID = c.Crime_Type_ID
GROUP BY c.Crime_Category
ORDER BY c.Crime_Category;

-- 10. Pivot / Cross-tabulation: Matrix of Victim Groups across Months (for latest Year)
SELECT 
    v.Victim_Group,
    SUM(CASE WHEN t.Month = 1 THEN f.Incident_Count ELSE 0 END) AS Jan_Incidents,
    SUM(CASE WHEN t.Month = 2 THEN f.Incident_Count ELSE 0 END) AS Feb_Incidents,
    SUM(CASE WHEN t.Month = 3 THEN f.Incident_Count ELSE 0 END) AS Mar_Incidents,
    SUM(CASE WHEN t.Month = 4 THEN f.Incident_Count ELSE 0 END) AS Apr_Incidents
FROM Fact_Crime_Incidents f
JOIN Dim_Time t ON f.Time_ID = t.Time_ID
JOIN Dim_Victim v ON f.Victim_ID = v.Victim_ID
WHERE t.Year = (SELECT MAX(Year) FROM Dim_Time)
GROUP BY v.Victim_Group
ORDER BY v.Victim_Group;
