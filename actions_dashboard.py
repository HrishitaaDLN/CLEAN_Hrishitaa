import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import json

# ---------------------
# 🌱 PAGE CONFIGURATION
# ---------------------
st.set_page_config(page_title="Sustainable Actions Dashboard", layout="wide", page_icon="🌱")
st.title("🌍 Sustainable Actions Dashboard")

# ---------------------
# 📂 LOAD DATA
# ---------------------
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

    with open("D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActionPrioritization/MostCommonPrioritisedActions/analysis_output_excel/Prioritized_Actions_and_Summary_final_clustered_actions.json") as f:
        data = json.load(f)
    df_json = pd.json_normalize(data, record_path='villages', meta=['action', 'category', 'justification'])
    df_json.columns = ['village', 'action', 'category', 'justification']

    return df1, df2, df_json

df1, df2, df_json = load_data()

# ---------------------
# 🔧 SIDEBAR FILTERS
# ---------------------
st.sidebar.header("🔧 Filters")
metric = st.sidebar.selectbox("Select Metric", ['Stationary Energy %', 'Waste %', 'Transport %'])
cities = st.sidebar.multiselect("Select Cities", options=df1['City'].unique(), default=df1['City'].unique())
filtered_df = df1[df1['City'].isin(cities)]

# ---------------------
# 📑 TABS
# ---------------------
tab1, tab2 = st.tabs(["Prioritized Actions", "Additional Visualizations"])

# ---------------------
# 📘 TAB 1: PRIORITIZED ACTIONS
# ---------------------
with tab1:
    st.header("📘 Prioritized Actions")

    # Metric Chart
    st.subheader(f"{metric} by City")
    fig = px.bar(filtered_df, x='City', y=metric, title=f"{metric} by City", template='plotly_dark')
    st.plotly_chart(fig, use_container_width=True)

    # Raw Data Table
    st.subheader("📋 Raw Data Table")
    st.dataframe(filtered_df, use_container_width=True)

    # High Priority Actions
    st.subheader("🔥 High Priority Stationary Energy Actions")
    high_priority_df = df2[(df2['Sector'] == 'Stationary Energy') & (df2['Priority Level_Clusters'] == 'High')]
    action_counts = high_priority_df['Village Name'].value_counts().reset_index()
    action_counts.columns = ['City', 'Action Count']

    col1, col2 = st.columns([2, 3])
    with col1:
        fig2 = px.bar(action_counts, x='City', y='Action Count', title="High Priority Actions per City", template='plotly_dark')
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.dataframe(high_priority_df[['Village Name', 'Action Description']], use_container_width=True)

    # Treemaps
    st.subheader("🧭 Treemaps for Action Breakdown")
    fig3 = px.treemap(
        high_priority_df,
        path=['Village Name'],
        values=high_priority_df['Village Name'].map(high_priority_df['Village Name'].value_counts()),
        title="Treemap of High Priority Actions by Village",
        template='plotly_dark'
    )
    st.plotly_chart(fig3, use_container_width=True)

    fig4 = px.treemap(
        high_priority_df,
        path=['Village Name', 'Action Description'],
        values=high_priority_df['Village Name'].map(high_priority_df['Village Name'].value_counts()),
        title="Treemap of Actions by Village & Description",
        template='plotly_dark'
    )
    st.plotly_chart(fig4, use_container_width=True)

    # 🔥 Radar Chart for Energy/Waste/Transport (df1)
    st.subheader("🕸️ Radar Chart for Selected Cities (Energy/Waste/Transport)")
    selected_radar_cities = st.multiselect(
        "Select up to 5 Cities for Radar Chart",
        options=df1['City'].unique(),
        default=df1['City'].unique()[:3]
    )
    radar_metrics = ['Stationary Energy %', 'Waste %', 'Transport %']
    radar_data = df1[df1['City'].isin(selected_radar_cities)][['City'] + radar_metrics]
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

# ---------------------
# 📘 TAB 2: EXTRACTED ACTIONS
# ---------------------
with tab2:
    st.header("📘 Additional Visualizations")
    # Pivot for JSON action category analysis
    pivot = df_json.groupby(['village', 'category']).size().unstack(fill_value=0)
    pivot['cluster'] = df_json.groupby('village')['action'].count()

    # 📊 Interactive Stacked Bar Chart
    st.subheader("📊 Action Category Breakdown by City (Select Cities)")
    selected_cities = st.multiselect(
        "Select up to 5 Cities to Display",
        options=pivot.index.tolist(),
        default=pivot.index.tolist()[:3],
        key="stacked_bar_multiselect"
    )

    if selected_cities:
        pivot_selected = pivot.loc[selected_cities].drop(columns='cluster').reset_index()
        pivot_long = pivot_selected.melt(id_vars='village', var_name='Category', value_name='Count')

        fig_stack_plotly = px.bar(
            pivot_long,
            x='village',
            y='Count',
            color='Category',
            title="Stacked Bar Chart: Action Categories by City",
            template='plotly_dark',
            labels={'village': 'City'},
        )
        fig_stack_plotly.update_layout(barmode='stack', xaxis_tickangle=-45)
        st.plotly_chart(fig_stack_plotly, use_container_width=True)
    else:
        st.info("Please select at least one city to display the stacked bar chart.")

    # 🌡️ Heatmap
    st.subheader("🌡️ Heatmap of Action Categories per Village")
    category_counts = df_json.groupby(['village', 'category']).size().unstack(fill_value=0)
    fig_heatmap, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(category_counts, annot=True, fmt="d", cmap="YlGnBu", ax=ax)
    ax.set_title("Cities vs Action Categories")
    ax.set_ylabel("City")
    ax.set_xlabel("Category")
    st.pyplot(fig_heatmap)

    # 🕸️ Radar Chart (JSON Action Categories)
    st.subheader("🕸️ Radar Chart of Action Categories for Selected Cities")
    selected_villages = st.multiselect(
        "Select up to 5 Villages (Cities) for Radar Chart",
        options=category_counts.index.tolist(),
        default=category_counts.index.tolist()[:3],
        key="radar_multiselect"
    )

    if selected_villages:
        radar_df = category_counts.loc[selected_villages].reset_index()
        radar_melted = radar_df.melt(id_vars='village', var_name='Category', value_name='Count')

        fig_radar = px.line_polar(
            radar_melted,
            r='Count',
            theta='Category',
            color='village',
            line_close=True,
            title="Radar Chart: Action Category Comparison by Village",
            template='plotly_dark'
        )
        fig_radar.update_traces(fill='toself')
        st.plotly_chart(fig_radar, use_container_width=True)
    else:
        st.info("Please select at least one village to display the radar chart.")
