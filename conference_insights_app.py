import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- File paths ---
path_scores = "/analysis_scores.xlsx"
path_extracted = "/merged_output.xlsx"
path_prioritized = "/Prioritized_Actions_and_Summary_final.xlsx"

# --- Load data ---
scores_df = pd.read_excel(path_scores)
extracted_df = pd.read_excel(path_extracted)
prioritized_df = pd.read_excel(path_prioritized)

# --- Strip all column names for safe access ---
scores_df.columns = scores_df.columns.str.strip()
extracted_df.columns = extracted_df.columns.str.strip()
prioritized_df.columns = prioritized_df.columns.str.strip()

# --- Normalize helper ---
def normalize(text):
    return str(text).strip().lower()

# --- Extract unique village names ---
villages_extracted = extracted_df['Village Name'].dropna().unique()
villages_prioritized = prioritized_df['Village Name'].dropna().unique()
all_villages = sorted(set(villages_extracted) | set(villages_prioritized))

# --- Title ---
st.title("City Climate Action Dashboard")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Extracted Actions", "Prioritized Actions", "Compare Cities"])

# === Tab 1: Overview ===
with tab1:
    st.subheader("Select a Village for Overview")
    selected_village_1 = st.selectbox("Village for Overview", sorted(scores_df['City'].dropna().unique()), key="village1")

    st.header("Matching Report(s) from Scores File")
    matched_scores = scores_df[scores_df['City'].str.lower().str.contains(normalize(selected_village_1), na=False)]

    if matched_scores.empty:
        st.warning(f"No reports found containing '{selected_village_1}'.")
    else:
        st.dataframe(matched_scores)

    st.subheader("Histogram of All Cities and Their Score")
    fig, ax = plt.subplots()
    ax.hist(scores_df['Total Score'], bins=10, edgecolor='black')
    ax.set_xlabel("Score")
    ax.set_ylabel("Number of Cities")
    ax.set_title("Distribution of Total Scores")
    st.pyplot(fig)

# === Tab 2: Extracted Actions ===
with tab2:
    st.subheader("Select a Village for Extracted Actions")
    selected_village_2 = st.selectbox("Village for Extracted Actions", all_villages, key="village2")

    extracted_filtered = extracted_df[extracted_df['Village Name'].str.lower() == normalize(selected_village_2)]

    st.header("Extracted Actions for Selected Village")
    st.dataframe(extracted_filtered)

    st.subheader("Histogram: Actions by Category")
    if not extracted_filtered.empty:
        bar_data = extracted_filtered['Category'].value_counts()
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.barh(bar_data.index, bar_data.values, color='skyblue')
        ax.set_xlabel("Count")
        ax.set_ylabel("Category")
        ax.set_title("Extracted Actions by Category")
        st.pyplot(fig)
    else:
        st.info("No extracted actions available for this village.")


# === Tab 3: Prioritized Actions ===
with tab3:
    st.subheader("Select a Village for Prioritized Actions")
    selected_village_3 = st.selectbox("Village for Prioritized Actions", all_villages, key="village3")

    prioritized_filtered = prioritized_df[prioritized_df['Village Name'].str.lower() == normalize(selected_village_3)]

    st.header("Prioritized Actions for Selected Village")
    st.dataframe(prioritized_filtered)

    if not prioritized_filtered.empty:
        if 'Sector' in prioritized_filtered.columns:
            st.subheader("Pie Chart: Actions by Sector")
            pie_data_cat = prioritized_filtered['Sector'].value_counts()
            fig1, ax1 = plt.subplots()
            ax1.pie(pie_data_cat, labels=pie_data_cat.index, autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)

        if 'Priority Level_Clusters' in prioritized_filtered.columns:
            st.subheader("Pie Chart: Priority Level Clusters")
            st.dataframe(prioritized_filtered[['Action Description', 'Priority Level_Clusters']])
            pie_data_priority = prioritized_filtered['Priority Level_Clusters'].value_counts()
            fig2, ax2 = plt.subplots()
            ax2.pie(pie_data_priority, labels=pie_data_priority.index, autopct='%1.1f%%', startangle=90)
            ax2.axis('equal')
            st.pyplot(fig2)
    else:
        st.info("No prioritized actions available for this village.")

# === Tab 4: Compare Cities ===
with tab4:
    st.subheader("Select Two Villages to Compare")
    col1, col2 = st.columns(2)
    with col1:
        village_a = st.selectbox("Village A", all_villages, key="compare_a")
    with col2:
        village_b = st.selectbox("Village B", all_villages, key="compare_b")

    def plot_bar_comparison(data_a, data_b, title, label_a, label_b):
        import numpy as np

        keys = sorted(set(data_a.index.tolist() + data_b.index.tolist()))
        vals_a = [data_a.get(k, 0) for k in keys]
        vals_b = [data_b.get(k, 0) for k in keys]

        x = np.arange(len(keys))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(x - width/2, vals_a, width, label=label_a)
        ax.bar(x + width/2, vals_b, width, label=label_b)

        ax.set_ylabel("Count")
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(keys, rotation=45, ha='right')
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)

    # --- Extracted Actions Comparison ---
    st.markdown("### Extracted Actions: Category Comparison")
    data_a_ex = extracted_df[extracted_df['Village Name'].str.lower() == normalize(village_a)]
    data_b_ex = extracted_df[extracted_df['Village Name'].str.lower() == normalize(village_b)]
    if not data_a_ex.empty or not data_b_ex.empty:
        count_a = data_a_ex['Category'].value_counts()
        count_b = data_b_ex['Category'].value_counts()
        plot_bar_comparison(count_a, count_b, "Extracted Action Categories", village_a, village_b)
    else:
        st.info("No extracted action data for selected villages.")

    # --- Prioritized Actions: Sector Comparison ---
    st.markdown("### Prioritized Actions: Sector Comparison")
    data_a_pr = prioritized_df[prioritized_df['Village Name'].str.lower() == normalize(village_a)]
    data_b_pr = prioritized_df[prioritized_df['Village Name'].str.lower() == normalize(village_b)]

    if 'Sector' in data_a_pr.columns and 'Sector' in data_b_pr.columns:
        count_a = data_a_pr['Sector'].value_counts()
        count_b = data_b_pr['Sector'].value_counts()
        if not count_a.empty or not count_b.empty:
            plot_bar_comparison(count_a, count_b, "Sector Distribution", village_a, village_b)
        else:
            st.info("No sector data for selected villages.")
    else:
        st.warning("Missing 'Sector' column.")

    # --- Prioritized Actions: Priority Level Cluster ---
    if 'Priority Level_Clusters' in data_a_pr.columns and 'Priority Level_Clusters' in data_b_pr.columns:
        st.markdown("### Prioritized Actions: Priority Level Comparison")
        count_a = data_a_pr['Priority Level_Clusters'].value_counts()
        count_b = data_b_pr['Priority Level_Clusters'].value_counts()
        if not count_a.empty or not count_b.empty:
            plot_bar_comparison(count_a, count_b, "Priority Level Clusters", village_a, village_b)
        else:
            st.info("No priority level data for selected villages.")
    else:
        st.warning("Missing 'Priority Level_Clusters' column.")
