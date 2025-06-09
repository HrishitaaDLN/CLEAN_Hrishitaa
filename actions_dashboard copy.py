import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(page_title="Sustainable Actions Dashboard", layout="wide", page_icon="🌱")

st.title("🌍 Sustainable Actions Dashboard")

# --- Load data ---
@st.cache_data
def load_data():
    df1 = pd.read_excel(
        "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractEnergyWasteTransport/action_output/Extracted_Actions_energywasteTransportPercent.xlsx",
        sheet_name="Category_Percent_Summary_by_Doc"
    )
    df1['City'] = df1['Source PDF'].str.replace('.pdf', '', regex=False)

    df2 = pd.read_excel(
        "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActionPrioritization/MostCommonPrioritisedActions/Prioritized_Actions_and_Summary_final.xlsx",
        sheet_name="Prioritized Actions"
    )
    return df1, df2

df1, df2 = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🔧 Filters")

metric = st.sidebar.selectbox("Select Metric", ['Stationary Energy %', 'Waste %', 'Transport %'])
cities = st.sidebar.multiselect("Select Cities", options=df1['City'].unique(), default=df1['City'].unique())

filtered_df = df1[df1['City'].isin(cities)]

# --- Metric Chart ---
st.subheader(f"{metric} by City")
fig = px.bar(filtered_df, x='City', y=metric, title=f"{metric} by City", template='plotly_dark')
st.plotly_chart(fig, use_container_width=True)

# --- Raw Data ---
st.subheader("📋 Raw Data Table")
st.dataframe(filtered_df, use_container_width=True)

# --- High Priority Actions ---
st.subheader("🔥 High Priority Stationary Energy Actions")

high_priority_df = df2[
    (df2['Sector'] == 'Stationary Energy') &
    (df2['Priority Level_Clusters'] == 'High')
]

action_counts = high_priority_df['Village Name'].value_counts().reset_index()
action_counts.columns = ['City', 'Action Count']

col1, col2 = st.columns([2, 3])

with col1:
    fig2 = px.bar(action_counts, x='City', y='Action Count', title="High Priority Actions per City", template='plotly_dark')
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.dataframe(high_priority_df[['Village Name', 'Action Description']], use_container_width=True)

# --- Treemaps Section ---
st.subheader("🧭 Treemaps for Action Breakdown")

# Treemap 1: Village Name
fig3 = px.treemap(
    high_priority_df,
    path=['Village Name'],
    values=high_priority_df['Village Name'].map(high_priority_df['Village Name'].value_counts()),
    title="Treemap of High Priority Actions by Village",
    template='plotly_dark'
)
st.plotly_chart(fig3, use_container_width=True)

# Treemap 2: Village + Action
fig4 = px.treemap(
    high_priority_df,
    path=['Village Name', 'Action Description'],
    values=high_priority_df['Village Name'].map(high_priority_df['Village Name'].value_counts()),
    title="Treemap of Actions by Village & Description",
    template='plotly_dark'
)
st.plotly_chart(fig4, use_container_width=True)

# Treemap 3 (Optional): Sector + Priority (if you want a broader view)
fig5 = px.treemap(
    df2,
    path=['Sector', 'Priority Level_Clusters'],
    values=df2['Sector'].map(df2['Sector'].value_counts()),
    title="Treemap of All Actions by Sector & Priority",
    template='plotly_dark'
)
st.plotly_chart(fig5, use_container_width=True)
# --- HEATMAP SECTION ---
st.subheader("🌡️ Heatmap of Metrics by City")

heatmap_data = df1[['City', 'Stationary Energy %', 'Waste %', 'Transport %']].set_index('City')
fig6 = px.imshow(
    heatmap_data,
    color_continuous_scale='Viridis',
    title="Heatmap: Energy, Waste, Transport % by City",
    labels=dict(color="Percentage"),
)
st.plotly_chart(fig6, use_container_width=True)

# --- RADAR/SPIDER CHART SECTION ---
st.subheader("🕸️ Radar Chart for Selected Cities")

# Let user pick up to 5 cities
selected_radar_cities = st.multiselect("Select up to 5 Cities for Radar Chart", options=df1['City'].unique(), default=df1['City'].unique()[:3])

# Prepare data
radar_metrics = ['Stationary Energy %', 'Waste %', 'Transport %']
radar_data = df1[df1['City'].isin(selected_radar_cities)][['City'] + radar_metrics]

# Melt for radar plot
melted = radar_data.melt(id_vars='City', var_name='Metric', value_name='Value')

fig7 = px.line_polar(
    melted, 
    r='Value', 
    theta='Metric', 
    color='City', 
    line_close=True,
    title="Radar Chart: City-wise Comparison",
    template='plotly_dark'
)
fig7.update_traces(fill='toself')
st.plotly_chart(fig7, use_container_width=True)


# =========================
# 📂 EXTRACTED ACTIONS
# =========================
st.markdown("## 📊 Additional Visualizations - Extracted Actions")

# --- 1. Stacked Bar Chart ---
st.subheader("Stacked % Contribution by Sector (City-wise)")
stack_data = df1[['City', 'Stationary Energy %', 'Waste %', 'Transport %']].set_index('City')
fig_stacked = px.bar(
    stack_data,
    x=stack_data.index,
    y=stack_data.columns,
    title="Stacked Bar Chart of Sectoral % per City",
    template='plotly_dark'
)
st.plotly_chart(fig_stacked, use_container_width=True)

# --- 2. Overall Sector Share (Pie Chart) ---
st.subheader("Total Share of Each Sector (Across All Cities)")
sector_sums = df1[['Stationary Energy %', 'Waste %', 'Transport %']].sum()
fig_pie = px.pie(
    values=sector_sums,
    names=sector_sums.index,
    title="Aggregate Sector % Across Cities",
    template='plotly_dark'
)
st.plotly_chart(fig_pie, use_container_width=True)

# --- 3. Grouped Bar Chart ---
st.subheader("Grouped Bar Chart of Sectoral % per City")
df_melted = df1.melt(id_vars='City', value_vars=['Stationary Energy %', 'Waste %', 'Transport %'],
                     var_name='Sector', value_name='Percentage')
fig_grouped = px.bar(df_melted, x='City', y='Percentage', color='Sector', barmode='group', template='plotly_dark')
st.plotly_chart(fig_grouped, use_container_width=True)

# =========================
# 🔥 PRIORITIZED ACTIONS
# =========================
st.markdown("## 🔥 Additional Visualizations - Prioritized Actions")

# --- 4. Action Count per Sector ---
st.subheader("Action Counts by Sector")
fig_sector_count = px.histogram(df2, x='Sector', color='Priority Level_Clusters', title="Number of Actions per Sector", template='plotly_dark')
st.plotly_chart(fig_sector_count, use_container_width=True)

# --- 5. Action Count by Priority ---
st.subheader("Action Counts by Priority Level")
fig_priority_count = px.histogram(df2, x='Priority Level_Clusters', color='Sector', title="Number of Actions by Priority", template='plotly_dark')
st.plotly_chart(fig_priority_count, use_container_width=True)

# --- 6. Sunburst Chart (Sector > Priority > Action) ---
st.subheader("Sunburst of Actions by Sector > Priority > Action")
sunburst_df = df2[['Sector', 'Priority Level_Clusters', 'Action Description']]
sunburst_df['count'] = 1  # needed for sizing
fig_sunburst = px.sunburst(sunburst_df, path=['Sector', 'Priority Level_Clusters', 'Action Description'], values='count',
                           title="Sunburst Chart of Action Breakdown", template='plotly_dark')
st.plotly_chart(fig_sunburst, use_container_width=True)


