import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Title and Description
st.set_page_config(page_title="Municipality Actions Dashboard", layout="wide")
st.title("Municipality Actions Analysis & Classification")
st.markdown("""
This app allows you to:
- Upload and explore municipality reports
- Filter reports based on scores
- Classify actions using GHG Protocol categories
- Visualize results interactively
- Refine categories and download final data
""")

# Step 1: Upload Data
st.header("1️⃣ Upload Municipality Report Data")
uploaded_file = st.file_uploader("Upload your Excel/CSV file", type=["csv", "xlsx"])

if uploaded_file:
    # Load data
    if uploaded_file.name.endswith("xlsx"):
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_csv(uploaded_file)

    st.subheader("📄 Raw Data Preview")
    st.write(df.head())

    # Step 2: Filter by Score
    st.header("2️⃣ Filter Reports by Score")
    if 'Score' in df.columns:
        min_score = st.slider("Select minimum score:", 1, 10, 5)
        filtered_df = df[df['Score'] >= min_score]
        st.write(f"### Filtered Reports (Score >= {min_score})", filtered_df)
    else:
        st.warning("No 'Score' column found in data.")

    # Step 3: Classify by GHG Protocol Category
    st.header("3️⃣ View Actions by GHG Protocol Category")
    if 'GHG Protocol Category' in df.columns:
        category_options = df['GHG Protocol Category'].dropna().unique().tolist()
        selected_category = st.selectbox("Select GHG Category", ["All"] + category_options)
        if selected_category == "All":
            st.write(df)
        else:
            st.write(df[df['GHG Protocol Category'] == selected_category])
    else:
        st.warning("No 'GHG Protocol Category' column found. Please ensure classification has been done.")

    # Step 4: Visualizations
    st.header("4️⃣ Visualizations")
    if 'GHG Protocol Category' in df.columns:
        # Bar Chart
        st.subheader("GHG Protocol Category - Bar Chart")
        fig1, ax1 = plt.subplots()
        df['GHG Protocol Category'].value_counts().plot(kind='bar', ax=ax1)
        st.pyplot(fig1)

        # Pie Chart
        st.subheader("GHG Protocol Category - Pie Chart")
        fig2, ax2 = plt.subplots(figsize=(30, 28))  # Increase figure size (width=10, height=8)
        df['GHG Protocol Category'].value_counts().plot(kind='pie', autopct='%1.2f%%', ax=ax2, fontsize=12)

        ax2.set_ylabel('')  # Remove y-axis label for a cleaner look
        ax2.set_title('Distribution of GHG Protocol Categories', fontsize=16)

        st.pyplot(fig2)


        # Top 10 Action Categories
        if 'Action Category' in df.columns:
            st.subheader("Top 10 Action Categories")
            top_10 = df['Action Category'].value_counts().head(10)
            fig3, ax3 = plt.subplots()
            top_10.plot(kind='barh', ax=ax3)
            ax3.invert_yaxis()
            st.pyplot(fig3)

    # Distribution Plot for Score
    if 'Score' in df.columns:
        st.subheader("Distribution of Document Scores")
        fig5, ax5 = plt.subplots()
        sns.histplot(df['Score'], bins=10, kde=True, ax=ax5)
        st.pyplot(fig5)

    # Step 5: Refine Categories
    st.header("5️⃣ Refine Categories (Editable Table)")
    st.write("Edit the categories directly below and download the updated file.")
    edited_df = st.data_editor(df, num_rows="dynamic")
    st.write("### Updated Data", edited_df)

    # Step 6: Download Final Data
    st.header("6️⃣ Download Refined Data")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        edited_df.to_excel(writer, index=False, sheet_name='Refined Data')
    st.download_button("📥 Download Refined Excel", data=buffer.getvalue(),
                       file_name="Refined_Actions.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("Please upload a data file to get started.")
