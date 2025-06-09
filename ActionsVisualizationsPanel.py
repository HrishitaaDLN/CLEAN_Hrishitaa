import panel as pn
import pandas as pd
import plotly.express as px

pn.extension('plotly', template='material')

# Load data
df1 = pd.read_excel(
    "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractEnergyWasteTransport/action_output/Extracted_Actions_energywasteTransportPercent.xlsx",
    sheet_name="Category_Percent_Summary_by_Doc"
)
df1['City'] = df1['Source PDF'].str.replace('.pdf', '', regex=False)

df2 = pd.read_excel(
    "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActionPrioritization/MostCommonPrioritisedActions/Prioritized_Actions_and_Summary_final.xlsx",
    sheet_name="Prioritized Actions"
)

# Widgets
metric_select = pn.widgets.Select(name='Metric', options=['Stationary Energy %', 'Waste %', 'Transport %'])
city_select = pn.widgets.MultiSelect(name='City Filter', options=sorted(df1['City'].unique()), size=10)

# Plot function
@pn.depends(city_select, metric_select)
def plot_metric(cities, metric):
    df_filtered = df1[df1['City'].isin(cities)] if cities else df1
    fig = px.bar(df_filtered, x='City', y=metric, title=f"{metric} by City", template='plotly_dark')
    return pn.pane.Plotly(fig)

# Table
table = pn.widgets.Tabulator(df1, pagination='remote', page_size=10)

# High-priority actions
high_priority_df = df2[
    (df2['Sector'] == 'Stationary Energy') &
    (df2['Priority Level_Clusters'] == 'High')
]
actions_table = pn.widgets.Tabulator(high_priority_df[['Village Name', 'Action Description']], pagination='remote', page_size=10)

def high_priority_bar():
    counts = high_priority_df['Village Name'].value_counts().reset_index()
    counts.columns = ['City', 'Action Count']
    fig = px.bar(counts, x='City', y='Action Count', title='High Priority Actions per City', template='plotly_dark')
    return pn.pane.Plotly(fig)

# Build dashboard layout
template = pn.template.MaterialTemplate(
    title="🌍 Sustainable Actions Dashboard",
    theme='dark',
    sidebar=[
        "## 🔧 Filters",
        metric_select,
        city_select
    ],
    main=[
        pn.Tabs(
            ("📊 Metric Chart", plot_metric),
            ("📋 Raw Data", table),
            ("🔥 High Priority Actions", pn.Column(high_priority_bar, actions_table))
        )
    ]
)

template.servable()
