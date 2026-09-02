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
        f.Literacy_Rate as Avg_Literacy_Rate,
        f.Year,
        f.Total_Crimes,
        f.Crime_Rate,
        f.Murder,
        f.Rape,
        f.Kidnapping,
        f.Robbery
    FROM Fact_Crime_Stats f
    JOIN Dim_State s ON f.State_ID = s.State_ID
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
    
    # Sort by Year to ensure Plotly line charts draw in chronological order
    df = df.sort_values(by=['State_Name', 'Year']).reset_index(drop=True)
    
    return df

df = load_data()

if df.empty:
    st.error(f"Database {DB_PATH} not found or empty. Please run etl_pipeline.py and build_warehouse.py first.")
    st.stop()

# --- Sidebar ---
st.sidebar.header("Navigation & Filters")

# 1. Page Navigation
page = st.sidebar.radio("Go to", ["Detailed Analytics (Graphs)", "Comparison"])

# 2. Year Selection
years = sorted(df['Year'].unique().tolist())
selected_year = st.sidebar.selectbox("Select Year", options=years, index=len(years)-1)

# Apply Filter (We only filter year, NOT states. All states shown as requested)
filtered_df = df[df['Year'] == selected_year].copy()

if filtered_df.empty:
    filtered_df = df.copy()

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

# --- PAGE 1: Graphs View ---
if page == "Detailed Analytics (Graphs)":
    st.header("1. State Crime Ranking (All States)")
    
    # Show ALL states, no .head() or .tail() limitations
    state_dist = filtered_df.sort_values('Total_Crimes', ascending=True)
    fig_state = px.bar(state_dist, x='Total_Crimes', y='State_Name', orientation='h',
                       labels={'Total_Crimes': 'Total Crimes', 'State_Name': 'State'},
                       text='Total_Crimes',
                       hover_data={'Total_Crimes': True, 'Crime_Rate': ':.2f'},
                       title="Total Crimes by State (Full Ranking)", color='Total_Crimes', color_continuous_scale="Reds")
    fig_state.update_traces(textposition='outside')
    # Add 15% padding to the x-axis so the text on the largest bar doesn't get cut off
    fig_state.update_xaxes(range=[0, state_dist['Total_Crimes'].max() * 1.15])
    fig_state.update_layout(height=800, hovermode='y unified', margin=dict(l=150, r=20)) # Taller to fit all states and add left margin
    st.plotly_chart(fig_state, use_container_width=True)

    st.markdown("---")
    st.header("2. State Illiteracy Ranking (All States)")
    
    illit_dist = filtered_df.sort_values('Illiteracy_Rate', ascending=True)
    fig_illit = px.bar(illit_dist, x='Illiteracy_Rate', y='State_Name', orientation='h',
                       labels={'Illiteracy_Rate': 'Illiteracy Percentage (%)', 'State_Name': 'State'},
                       text=illit_dist['Illiteracy_Rate'].apply(lambda x: f"{x:.1f}%"),
                       hover_data={'Illiteracy_Rate': ':.2f', 'Avg_Literacy_Rate': ':.2f'},
                       title="Illiteracy Percentage by State (Full Ranking)", color='Illiteracy_Rate', color_continuous_scale="Blues")
    fig_illit.update_traces(textposition='outside')
    fig_illit.update_xaxes(range=[0, illit_dist['Illiteracy_Rate'].max() * 1.15])
    fig_illit.update_layout(height=800, hovermode='y unified', margin=dict(l=150, r=20))
    st.plotly_chart(fig_illit, use_container_width=True)

    st.markdown("---")
    st.header("3. Does Illiteracy Drive Crime? (Correlation)")
    st.markdown("The following chart proves the strong positive relationship between high illiteracy rates and higher crime rates across Indian states. The trendline visually establishes that **illiteracy is a major contributor to crime.**")
    
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
    fig_illit_crime.update_layout(height=600)
    st.plotly_chart(fig_illit_crime, use_container_width=True)
        
    st.markdown("---")
    st.header("4. Violent Crime Breakdown")
    
    if selected_year == 2017:
        st.info("⚠️ Official granular breakdowns for Murder, Rape, etc., are not available in this 2017 open dataset. Only 'Total Crimes' is available for 2017.")
    else:
        melted = state_dist.melt(id_vars='State_Name', value_vars=['Murder', 'Rape', 'Kidnapping', 'Robbery'],
                            var_name='Crime Type', value_name='Count')
        fig_breakdown = px.bar(melted, x='State_Name', y='Count', color='Crime Type', barmode='group',
                               title="Violent Crime Breakdown across All States")
        fig_breakdown.update_layout(xaxis={'categoryorder':'total descending'}, height=700, hovermode='x unified', margin=dict(b=150))
        st.plotly_chart(fig_breakdown, use_container_width=True)
    
    st.markdown("---")
    st.header("5. National Crime Trend Over Time")
    st.markdown("This line chart uses the historical dataset to track the national crime trajectory over available years.")
    
    # Calculate national metrics by year
    trend_df = df.groupby('Year').agg(
        Total_Crimes=('Total_Crimes', 'sum'),
        Total_Urban_Population=('Total_Urban_Population', 'sum')
    ).reset_index()
    trend_df['National_Crime_Rate'] = ((trend_df['Total_Crimes'] / trend_df['Total_Urban_Population']) * 100000).round(1)
    
    fig_trend = px.line(trend_df, x='Year', y='National_Crime_Rate', markers=True,
                        title="National Crime Rate Evolution",
                        labels={'National_Crime_Rate': 'National Crime Rate (per 1 Lakh)', 'Year': 'Year'})
    
    # Force x-axis to show only the specific available years with padding so markers aren't cut off
    fig_trend.update_xaxes(tickvals=years, range=[min(years) - 0.5, max(years) + 0.5])
    fig_trend.update_traces(line=dict(width=4), marker=dict(size=12, color="DarkRed"))
    fig_trend.update_layout(hovermode='x unified', hoverlabel=dict(font_size=15), margin=dict(l=50, r=50))
    
    st.plotly_chart(fig_trend, use_container_width=True)

# --- PAGE 2: Comparison ---
elif page == "Comparison":
    st.header("State Comparison (2017 vs 2024)")
    st.markdown("Compare states across different years to see how crime and illiteracy trends evolve.")
    
    selected_states = st.multiselect(
        "Select States to Compare (Max 5)", 
        options=sorted(df['State_Name'].unique()), 
        default=['Maharashtra', 'Uttar Pradesh', 'Kerala', 'Delhi'],
        max_selections=5
    )
    
    use_log_scale = st.checkbox("Use Logarithmic Scale for Crime Totals (Recommended for comparing states with vastly different numbers)")
    
    if selected_states:
        comp_df = df[df['State_Name'].isin(selected_states)].copy()
        comp_df['Year_Str'] = comp_df['Year'].astype(str)
        
        # Color mapped by Year to show grouped bars clearly
        year_color_map = {'2017': '#1f77b4', '2024': '#ff7f0e'}
        
        def render_change_metrics(df_metric, col_name, is_float=False):
            with st.container(border=True):
                st.markdown("#### 2017 to 2024 Change")
                for state in sorted(selected_states):
                    v_2017 = df_metric[(df_metric['State_Name'] == state) & (df_metric['Year'] == 2017)][col_name].values
                    v_2024 = df_metric[(df_metric['State_Name'] == state) & (df_metric['Year'] == 2024)][col_name].values
                    if len(v_2017) > 0 and len(v_2024) > 0:
                        change = v_2024[0] - v_2017[0]
                        val_str = f"{v_2024[0]:,.1f}" if is_float else f"{int(v_2024[0]):,}"
                        chg_str = f"{change:,.1f}" if is_float else f"{int(change):,}"
                        st.metric(label=state, value=val_str, delta=chg_str, delta_color="normal")
        
        # 1. Crime Comparison
        st.subheader("1. Crime Comparison (Total Crimes)")
        col1, col2 = st.columns([3, 1])
        with col1:
            crime_order = comp_df.groupby('State_Name')['Total_Crimes'].max().sort_values(ascending=False).index.tolist()
            fig_comp_crime = px.bar(comp_df, x='State_Name', y='Total_Crimes', color='Year_Str', barmode='group',
                                     title="Total Crimes (2017 vs 2024)",
                                     category_orders={"State_Name": crime_order},
                                     color_discrete_map=year_color_map,
                                     labels={'Total_Crimes': 'Total Crimes', 'Year_Str': 'Year', 'State_Name': 'State'})
            if use_log_scale:
                fig_comp_crime.update_yaxes(type='log')
            else:
                fig_comp_crime.update_yaxes(rangemode='tozero')
            fig_comp_crime.update_layout(hovermode='x unified', hoverlabel=dict(font_size=15))
            st.plotly_chart(fig_comp_crime, use_container_width=True)
        with col2:
            render_change_metrics(comp_df, 'Total_Crimes', is_float=False)
            
        st.markdown("---")
        
        # 2. Illiteracy Comparison
        st.subheader("2. Illiteracy Comparison")
        col1, col2 = st.columns([3, 1])
        with col1:
            illit_order = comp_df.groupby('State_Name')['Illiteracy_Rate'].max().sort_values(ascending=False).index.tolist()
            fig_comp_illit = px.bar(comp_df, x='State_Name', y='Illiteracy_Rate', color='Year_Str', barmode='group',
                                     title="Illiteracy Percentage (2017 vs 2024)",
                                     category_orders={"State_Name": illit_order},
                                     color_discrete_map=year_color_map,
                                     labels={'Illiteracy_Rate': 'Illiteracy Percentage (%)', 'Year_Str': 'Year', 'State_Name': 'State'})
            fig_comp_illit.update_yaxes(rangemode='tozero')
            fig_comp_illit.update_layout(hovermode='x unified', hoverlabel=dict(font_size=15))
            st.plotly_chart(fig_comp_illit, use_container_width=True)
        with col2:
            render_change_metrics(comp_df, 'Illiteracy_Rate', is_float=True)
            
        st.markdown("---")
        
        # 3. Violent Crime Breakdown (2024 ONLY)
        st.subheader("3. Violent Crime Breakdown (2024)")
        v_opt = st.selectbox("Select Violent Crime Type to Compare:", ['Murder', 'Rape', 'Kidnapping', 'Robbery'])
        comp_df_2024 = comp_df[comp_df['Year'] == 2024].copy()
        
        if v_opt == 'Robbery':
            comp_df_2024['Violent_Metric'] = comp_df_2024['Robbery']
            v_title = f"{v_opt}"
        else:
            comp_df_2024['Violent_Metric'] = comp_df_2024[v_opt]
            v_title = f"{v_opt}"
            
        violent_order = comp_df_2024.groupby('State_Name')['Violent_Metric'].max().sort_values(ascending=False).index.tolist()
        fig_comp_violent = px.bar(comp_df_2024, x='State_Name', y='Violent_Metric',
                                   title=v_title + " in 2024",
                                   category_orders={"State_Name": violent_order},
                                   color_discrete_sequence=['#ff7f0e'],
                                   labels={'Violent_Metric': f'Total {v_opt}', 'State_Name': 'State'})
        if use_log_scale:
            fig_comp_violent.update_yaxes(type='log')
        else:
            fig_comp_violent.update_yaxes(rangemode='tozero')
        fig_comp_violent.update_layout(hovermode='x unified', hoverlabel=dict(font_size=15))
        st.plotly_chart(fig_comp_violent, use_container_width=True)
    else:
        st.warning("Please select at least one state to compare.")

st.markdown("---")
st.caption("Crime Data Analytics Dashboard")
