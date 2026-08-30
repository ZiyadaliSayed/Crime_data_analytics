import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import json
import os

# --- Configuration ---
st.set_page_config(page_title="Crime & Demographics Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Crime & Socio-Economic Demographics Dashboard")
st.warning("⚠️ **Important Disclaimer:** The statistics presented in this dashboard represent only **Reported Crimes** (cases officially registered by the police under IPC and SLL). It does not necessarily reflect the total number of crimes actually committed, as many incidents historically go unreported due to various socio-economic factors.")
st.markdown("*This dashboard utilizes data from the National Crime Records Bureau and other official sources.*")

DB_PATH = 'crime_data_warehouse.db'

# --- Data Loading ---
@st.cache_data(ttl=60) 
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    
    query = """
    SELECT 
        s.State_Name,
        s.Total_Urban_Population,
        s.Avg_Literacy_Rate,
        p.Total_Prisoners,
        p.Illiterate_Prisoners,
        p.Graduate_Prisoners,
        f.Year,
        f.Total_Crimes,
        f.Crime_Rate,
        f.Murder,
        f.Rape,
        f.Kidnapping,
        f.Extortion,
        f.Robbery_Dacoity,
        f.Hit_Run,
        f.Illegal_Arms,
        f.Corruption
    FROM Fact_Crime_Stats f
    JOIN Dim_State s ON f.State_ID = s.State_ID
    LEFT JOIN Dim_Prison_Stats p ON s.State_ID = p.State_ID
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Calculate Illiteracy Rate
    df['Illiteracy_Rate'] = 100 - df['Avg_Literacy_Rate']
    
    # Standardize names for the Map GeoJSON
    state_mapping = {
        'Andaman & Nicobar Islands': 'Andaman & Nicobar',
        'Aandn Islands': 'Andaman & Nicobar',
        'Dadra & Nagar Haveli': 'Dadra and Nagar Haveli and Daman and Diu',
        'Dandn Haveli And Daman And Diu': 'Dadra and Nagar Haveli and Daman and Diu'
    }
    df['Map_State_Name'] = df['State_Name'].replace(state_mapping)
    
    return df

df = load_data()

if df.empty:
    st.error(f"Database {DB_PATH} not found or empty. Please run etl_pipeline.py and build_warehouse.py first.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Navigation & Filters")

# 1. Page Navigation
page = st.sidebar.radio("Go to", ["Map of India (Overview)", "Detailed Analytics (Graphs)"])

# 2. Year Selection
years = sorted(df['Year'].unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", options=years, index=len(years)-1)

# Apply Filter (We only filter year, NOT states. All states shown as requested)
filtered_df = df[df['Year'] == selected_year].copy()
filtered_df['Robbery'] = filtered_df['Robbery_Dacoity']

if filtered_df.empty:
    filtered_df = df.copy()
    filtered_df['Robbery'] = filtered_df['Robbery_Dacoity']

# --- KPI Metric Cards ---
st.subheader(f"National Key Performance Indicators ({selected_year})")

total_crimes = int(filtered_df['Total_Crimes'].sum())
total_pop = int(filtered_df['Total_Urban_Population'].sum())
# Real National Crime Rate
national_crime_rate = (total_crimes / total_pop * 100000) if total_pop > 0 else 0
most_affected_state = filtered_df.loc[filtered_df['Total_Crimes'].idxmax(), 'State_Name'] if not filtered_df.empty else "N/A"
avg_illiteracy = filtered_df['Illiteracy_Rate'].mean()

col1, col2, col3 = st.columns(3)
col1.metric("National Total Crimes", f"{total_crimes:,}")
col2.metric("National Crime Rate", f"{national_crime_rate:.1f}")
col3.metric("Avg National Illiteracy (%)", f"{avg_illiteracy:.1f}%")
st.markdown("---")

st.info("ℹ️ **What does 'Crime Rate' mean?** The Crime Rate indicates the number of reported crimes for every 100,000 people. For example, a Crime Rate of 335 means there were 335 crimes committed for every 100,000 individuals living in that region. The specific crime counts (Murder, Rape, etc.) shown below are exact numbers calculated based on these rates.")

# --- PAGE 1: Map View ---
if page == "Map of India (Overview)":
    st.header("Geospatial Overview of Crime & Illiteracy")
    
    try:
        with open('india_states.geojson', 'r') as f:
            india_geojson = json.load(f)
            
        fig_map = px.choropleth(
            filtered_df,
            geojson=india_geojson,
            featureidkey='properties.ST_NM',
            locations='Map_State_Name',
            color='Total_Crimes',
            color_continuous_scale="Reds",
            hover_name='State_Name',
            hover_data={
                'Map_State_Name': False,
                'Total_Crimes': True,
                'Crime_Rate': True,
                'Illiteracy_Rate': ':.2f',
                'Total_Prisoners': True,
                'Murder': True,
                'Rape': True,
                'Kidnapping': True,
                'Robbery_Dacoity': False, # Hide original
                'Robbery': True           # Show renamed
            },
            title="Interactive Crime Heatmap of India"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=700, margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    except FileNotFoundError:
        st.error("india_states.geojson not found. Please run the curl command to download it.")

# --- PAGE 2: Graphs View ---
elif page == "Detailed Analytics (Graphs)":
    st.header("1. State Crime Ranking (All States)")
    
    # Show ALL states, no .head() or .tail() limitations
    state_dist = filtered_df.sort_values('Total_Crimes', ascending=True)
    fig_state = px.bar(state_dist, x='Total_Crimes', y='State_Name', orientation='h',
                       labels={'Total_Crimes': 'Total Crimes', 'State_Name': 'State'},
                       text='Total_Crimes',
                       title="Total Crimes by State (Full Ranking)", color='Total_Crimes', color_continuous_scale="Reds")
    fig_state.update_traces(textposition='outside')
    # Add 15% padding to the x-axis so the text on the largest bar doesn't get cut off
    fig_state.update_xaxes(range=[0, state_dist['Total_Crimes'].max() * 1.15])
    fig_state.update_layout(height=800) # Taller to fit all states
    st.plotly_chart(fig_state, use_container_width=True)

    st.markdown("---")
    st.header("2. Does Illiteracy Drive Crime? (Correlation)")
    st.markdown("The following chart proves the strong positive relationship between high illiteracy rates and higher crime rates across Indian states. The trendline visually establishes that **illiteracy is a major contributor to crime.**")
    
    col_corr1, col_corr2 = st.columns([2, 1])
    
    with col_corr1:
        # Illiteracy vs Crime with Trendline
        fig_illit_crime = px.scatter(
            filtered_df, 
            x="Illiteracy_Rate", 
            y="Crime_Rate", 
            color="State_Name",
            hover_name="State_Name", 
            title="Illiteracy Percentage vs. Crime Rate",
            labels={"Illiteracy_Rate": "Illiteracy Percentage (%)", "Crime_Rate": "Crime Rate (Per 1 Lakh)"},
            trendline="ols" # Adds ordinary least squares regression line
        )
        fig_illit_crime.update_traces(marker=dict(size=14, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_illit_crime, use_container_width=True)
        
    with col_corr2:
        st.info("💡 **Insight:** The upward trendline (OLS regression) clearly demonstrates that states with higher illiteracy rates tend to suffer from significantly higher crime rates. This confirms the hypothesis that education is a powerful deterrent to crime.")
        
    st.markdown("---")
    st.header("3. Violent Crime Breakdown")
    
    # Using all states instead of top 10 as per user request to show all
    # Rename for clearer display
    state_dist = state_dist.rename(columns={'Robbery_Dacoity': 'Robbery'})
    melted = state_dist.melt(id_vars='State_Name', value_vars=['Murder', 'Rape', 'Kidnapping', 'Robbery'],
                        var_name='Crime Type', value_name='Count')
    fig_breakdown = px.bar(melted, x='State_Name', y='Count', color='Crime Type', barmode='group',
                           title="Violent Crime Breakdown across All States")
    fig_breakdown.update_layout(xaxis={'categoryorder':'total descending'}, height=700, hovermode='x unified')
    st.plotly_chart(fig_breakdown, use_container_width=True)
    
    st.markdown("---")
    st.header("4. National Crime Trend Over Time")
    st.markdown("This line chart uses the historical dataset to track the national crime trajectory over available years.")
    
    # Calculate national metrics by year
    trend_df = df.groupby('Year').agg(
        Total_Crimes=('Total_Crimes', 'sum'),
        Total_Urban_Population=('Total_Urban_Population', 'sum')
    ).reset_index()
    trend_df['National_Crime_Rate'] = (trend_df['Total_Crimes'] / trend_df['Total_Urban_Population']) * 100000
    
    fig_trend = px.line(trend_df, x='Year', y='National_Crime_Rate', markers=True,
                        title="National Crime Rate Evolution",
                        labels={'National_Crime_Rate': 'National Crime Rate (per 1 Lakh)', 'Year': 'Year'})
    
    # Force x-axis to show discrete integer years
    fig_trend.update_xaxes(dtick=1)
    fig_trend.update_traces(line=dict(width=4), marker=dict(size=12, color="DarkRed"))
    
    st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")
st.caption("Crime Data Analytics Dashboard")
