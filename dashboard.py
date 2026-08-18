import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- Configuration ---
st.set_page_config(page_title="Crime & Demographics Dashboard", page_icon="🛡️", layout="wide")
st.title("🛡️ Crime & Socio-Economic Demographics Dashboard")

DB_PATH = 'crime_data_warehouse.db'

# --- Data Loading ---
# Note: clearing the cache helps see the latest database changes!
@st.cache_data(ttl=1) 
def load_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Main Fact Query
    query = """
    SELECT 
        f.Incident_ID,
        f.Incident_Count,
        t.Year,
        t.Month,
        l.State,
        l.City,
        l.Population,
        v.Victim_Group,
        o.Demographic AS Offender_Demographic,
        c.Crime_Category
    FROM Fact_Crime_Incidents f
    LEFT JOIN Dim_Time t ON f.Time_ID = t.Time_ID
    LEFT JOIN Dim_Location l ON f.Location_ID = l.Location_ID
    LEFT JOIN Dim_Victim v ON f.Victim_ID = v.Victim_ID
    LEFT JOIN Dim_Offender o ON f.Offender_ID = o.Offender_ID
    LEFT JOIN Dim_Crime_Profile c ON f.Crime_Type_ID = c.Crime_Type_ID
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 2. Supplementary Data (Demographics & Prison Stats)
    demo_df = pd.read_csv('indian_cities_demographics.csv')
    demo_df.columns = demo_df.columns.str.strip()
    
    prison_df = pd.read_csv('indian_prison_statistics.csv')
    prison_df.columns = prison_df.columns.str.strip()
    
    return df, demo_df, prison_df

df, demo_df, prison_df = load_data()

if df.empty:
    st.error(f"Database {DB_PATH} not found or empty. Please run build_warehouse.py first.")
    st.stop()

# Clean demographics for State-level merging
if not demo_df.empty:
    demo_df['state_name'] = demo_df['state_name'].astype(str).str.strip().str.title()
    state_literacy = demo_df.groupby('state_name')['effective_literacy_rate_total'].mean().reset_index()
    state_literacy.rename(columns={'state_name': 'State', 'effective_literacy_rate_total': 'Literacy_Rate'}, inplace=True)
else:
    state_literacy = pd.DataFrame(columns=['State', 'Literacy_Rate'])

# Clean prison stats
if not prison_df.empty:
    prison_df['State/UT'] = prison_df['State/UT'].astype(str).str.strip().str.title()
    prison_stats = prison_df[['State/UT', 'Educational Standard - Illiterate', 'Educational Standard - Graduate', 'Total - Total']].copy()
    prison_stats.rename(columns={
        'State/UT': 'State',
        'Total - Total': 'Total_Prisoners',
        'Educational Standard - Illiterate': 'Illiterate_Prisoners',
        'Educational Standard - Graduate': 'Graduate_Prisoners'
    }, inplace=True)
else:
    prison_stats = pd.DataFrame(columns=['State', 'Total_Prisoners', 'Illiterate_Prisoners', 'Graduate_Prisoners'])


# --- Sidebar Filters ---
st.sidebar.header("Filters")

years = sorted(df['Year'].dropna().unique().tolist())
selected_years = st.sidebar.multiselect("Select Year(s)", options=years, default=years)

states = sorted(df['State'].dropna().unique().tolist())
selected_states = st.sidebar.multiselect("Select State(s)", options=states, default=states)

categories = sorted(df['Crime_Category'].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect("Select Crime Category", options=categories, default=categories)

# Apply Filters
filtered_df = df[
    (df['Year'].isin(selected_years)) &
    (df['State'].isin(selected_states)) &
    (df['Crime_Category'].isin(selected_categories))
]

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --- KPI Metric Cards ---
st.subheader("Key Performance Indicators")

total_incidents = int(filtered_df['Incident_Count'].sum())
top_category = filtered_df.groupby('Crime_Category')['Incident_Count'].sum().idxmax() if not filtered_df.empty else "N/A"
most_affected_state = filtered_df.groupby('State')['Incident_Count'].sum().idxmax() if not filtered_df.empty else "N/A"
highest_risk_demo = filtered_df.groupby('Victim_Group')['Incident_Count'].sum().idxmax() if not filtered_df.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Incidents", f"{total_incidents:,}")
col2.metric("Top Crime Category", top_category)
col3.metric("Most Affected State", most_affected_state)
col4.metric("Highest Risk Victim Demo", highest_risk_demo)

st.markdown("---")

# --- Visualizations ---
st.header("1. Core Crime Analytics")
col_left, col_right = st.columns(2)

with col_left:
    # Monthly Incident Trend
    st.subheader("Monthly Incident Trend")
    monthly_trend = filtered_df.groupby(['Year', 'Month'])['Incident_Count'].sum().reset_index()
    monthly_trend['YearMonth'] = monthly_trend['Year'].astype(str) + "-" + monthly_trend['Month'].astype(str).str.zfill(2)
    monthly_trend = monthly_trend.sort_values('YearMonth')
    fig_trend = px.line(monthly_trend, x='YearMonth', y='Incident_Count', markers=True,
                        labels={'YearMonth': 'Time (Year-Month)', 'Incident_Count': 'Total Incidents'},
                        title="Incident Trend Over Time")
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # State-wise Distribution
    st.subheader("State-wise Distribution")
    state_dist = filtered_df.groupby('State')['Incident_Count'].sum().reset_index().sort_values('Incident_Count', ascending=True)
    if len(state_dist) > 15:
        state_dist = state_dist.tail(15)
        title_state = "Top 15 States by Total Incidents"
    else:
        title_state = "Incidents by State"
    fig_state = px.bar(state_dist, x='Incident_Count', y='State', orientation='h',
                       labels={'Incident_Count': 'Total Incidents', 'State': 'State'},
                       title=title_state, color='Incident_Count', color_continuous_scale="Reds")
    st.plotly_chart(fig_state, use_container_width=True)

with col_right:
    # Crime Category Breakdown
    st.subheader("Crime Category Breakdown")
    cat_breakdown = filtered_df.groupby('Crime_Category')['Incident_Count'].sum().reset_index().sort_values('Incident_Count', ascending=False)
    fig_cat = px.bar(cat_breakdown, x='Crime_Category', y='Incident_Count',
                     labels={'Incident_Count': 'Total Incidents', 'Crime_Category': 'Category'},
                     title="Incidents by Crime Category", color='Crime_Category')
    st.plotly_chart(fig_cat, use_container_width=True)
    
    # OLAP Cross-tabulation Heatmap
    st.subheader("OLAP Cross-Tabulation (Category vs Month)")
    heatmap_data = filtered_df.pivot_table(index='Crime_Category', columns='Month', values='Incident_Count', aggfunc='sum', fill_value=0)
    fig_heat = px.imshow(heatmap_data, text_auto=True, aspect="auto",
                         labels=dict(x="Month", y="Crime Category", color="Incidents"),
                         title="Incidents Heatmap (Month vs Category)",
                         color_continuous_scale="Blues")
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")
st.header("2. Socio-Economic Correlations")

# Merge state_dist with demographics
state_agg = filtered_df.groupby('State').agg({'Incident_Count': 'sum', 'Population': 'mean'}).reset_index()
state_merged = pd.merge(state_agg, state_literacy, on='State', how='inner')
state_merged = pd.merge(state_merged, prison_stats, on='State', how='inner')

if not state_merged.empty:
    st.markdown("### Literacy Rate vs. Crime & Prison Statistics")
    st.write("Does a lower literacy rate correlate with higher crime or a larger prison population? Let's explore the data.")
    
    col_corr1, col_corr2 = st.columns(2)
    
    with col_corr1:
        # Literacy Rate vs Incident Count (Scatter)
        fig_lit_crime = px.scatter(state_merged, x="Literacy_Rate", y="Incident_Count", size="Population", color="State",
                                   hover_name="State", title="Literacy Rate vs. Total Crime Incidents",
                                   labels={"Literacy_Rate": "Average Literacy Rate (%)", "Incident_Count": "Total Incidents"})
        st.plotly_chart(fig_lit_crime, use_container_width=True)
        
        # Educational Background of Prisoners (Bar)
        st.subheader("Prisoner Educational Background by State")
        prison_edu = state_merged[['State', 'Illiterate_Prisoners', 'Graduate_Prisoners']].melt(id_vars='State', var_name='Education Level', value_name='Prisoner Count')
        fig_edu = px.bar(prison_edu, x='State', y='Prisoner Count', color='Education Level', barmode='group',
                         title="Illiterate vs Graduate Prisoners per State")
        st.plotly_chart(fig_edu, use_container_width=True)

    with col_corr2:
        # Literacy Rate vs Prison Population
        fig_lit_prison = px.scatter(state_merged, x="Literacy_Rate", y="Total_Prisoners", size="Total_Prisoners", color="State",
                                    hover_name="State", title="Literacy Rate vs. Total Prison Population",
                                    labels={"Literacy_Rate": "Average Literacy Rate (%)", "Total_Prisoners": "Total Prison Population"})
        st.plotly_chart(fig_lit_prison, use_container_width=True)
        
        # Literacy Rate Map/Bar (Lowest to Highest)
        state_merged_sorted = state_merged.sort_values('Literacy_Rate', ascending=True)
        fig_lit_bar = px.bar(state_merged_sorted, x='Literacy_Rate', y='State', orientation='h',
                             title="States Ranked by Literacy Rate (Lowest to Highest)",
                             labels={'Literacy_Rate': 'Literacy Rate (%)'}, color='Literacy_Rate', color_continuous_scale="Viridis")
        st.plotly_chart(fig_lit_bar, use_container_width=True)

else:
    st.info("Not enough demographic overlap data found to generate correlation charts for the selected states.")

st.markdown("---")
st.caption("Crime Data Analytics Dashboard - Powered by Streamlit & Plotly")
