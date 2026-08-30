-- crime_data_warehouse.db Schema
-- Represents a clean, aggregated Star Schema for Indian Crime Statistics (2023)

DROP TABLE IF EXISTS Fact_Crime_Stats;
DROP TABLE IF EXISTS Dim_Prison_Stats;
DROP TABLE IF EXISTS Dim_State;

CREATE TABLE Dim_State (
    State_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    State_Name TEXT UNIQUE NOT NULL,
    Total_Urban_Population INTEGER,
    Avg_Literacy_Rate REAL
);

CREATE TABLE Dim_Prison_Stats (
    Prison_Stat_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    State_ID INTEGER NOT NULL,
    Total_Prisoners INTEGER,
    Illiterate_Prisoners INTEGER,
    Graduate_Prisoners INTEGER,
    FOREIGN KEY(State_ID) REFERENCES Dim_State(State_ID)
);

CREATE TABLE Fact_Crime_Stats (
    Fact_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    State_ID INTEGER NOT NULL,
    Year INTEGER NOT NULL,
    Total_Crimes INTEGER,
    Crime_Rate REAL,
    Murder INTEGER,
    Rape INTEGER,
    Kidnapping INTEGER,
    Extortion INTEGER,
    Robbery_Dacoity INTEGER,
    Hit_Run INTEGER,
    Illegal_Arms INTEGER,
    Corruption INTEGER,
    FOREIGN KEY(State_ID) REFERENCES Dim_State(State_ID)
);
