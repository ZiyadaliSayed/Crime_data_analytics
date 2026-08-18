-- Drop tables if they exist
DROP TABLE IF EXISTS Fact_Crime_Incidents;
DROP TABLE IF EXISTS Dim_Time;
DROP TABLE IF EXISTS Dim_Location;
DROP TABLE IF EXISTS Dim_Victim;
DROP TABLE IF EXISTS Dim_Offender;
DROP TABLE IF EXISTS Dim_Crime_Profile;

-- Dimension: Time
CREATE TABLE Dim_Time (
    Time_ID INTEGER PRIMARY KEY,
    Year INTEGER,
    Month INTEGER,
    Day_of_Week TEXT
);

-- Dimension: Location
CREATE TABLE Dim_Location (
    Location_ID INTEGER PRIMARY KEY,
    State TEXT,
    City TEXT,
    Population INTEGER
);

-- Dimension: Victim
CREATE TABLE Dim_Victim (
    Victim_ID INTEGER PRIMARY KEY,
    Victim_Group TEXT
);

-- Dimension: Offender
CREATE TABLE Dim_Offender (
    Offender_ID INTEGER PRIMARY KEY,
    Demographic TEXT
);

-- Dimension: Crime Profile
CREATE TABLE Dim_Crime_Profile (
    Crime_Type_ID INTEGER PRIMARY KEY,
    Crime_Category TEXT
);

-- Fact: Crime Incidents
CREATE TABLE Fact_Crime_Incidents (
    Incident_ID INTEGER PRIMARY KEY,
    Time_ID INTEGER,
    Location_ID INTEGER,
    Victim_ID INTEGER,
    Offender_ID INTEGER,
    Crime_Type_ID INTEGER,
    Incident_Count INTEGER,
    FOREIGN KEY (Time_ID) REFERENCES Dim_Time(Time_ID),
    FOREIGN KEY (Location_ID) REFERENCES Dim_Location(Location_ID),
    FOREIGN KEY (Victim_ID) REFERENCES Dim_Victim(Victim_ID),
    FOREIGN KEY (Offender_ID) REFERENCES Dim_Offender(Offender_ID),
    FOREIGN KEY (Crime_Type_ID) REFERENCES Dim_Crime_Profile(Crime_Type_ID)
);

-- Indexes for Fact Table Foreign Keys to improve JOIN performance
CREATE INDEX idx_fact_time ON Fact_Crime_Incidents(Time_ID);
CREATE INDEX idx_fact_location ON Fact_Crime_Incidents(Location_ID);
CREATE INDEX idx_fact_victim ON Fact_Crime_Incidents(Victim_ID);
CREATE INDEX idx_fact_offender ON Fact_Crime_Incidents(Offender_ID);
CREATE INDEX idx_fact_crime_profile ON Fact_Crime_Incidents(Crime_Type_ID);
