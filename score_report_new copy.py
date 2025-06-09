from docx import Document
from pathlib import Path
import pandas as pd
import re
import google.generativeai as genai
from datetime import datetime

def analyze_questionnaire_reports(folder_path: str, api_key: str) -> None:
    genai.configure(api_key=api_key)

    # Define all question labels
    questions = [f"{i}.{j}" for i, n in zip(range(1, 5), [7, 7, 5, 5]) for j in range(1, n + 1)]
    categories = {
        "Energy Emissions Inventory": questions[0:7],
        "Strategy Identification": questions[7:14],
        "Action Prioritization & Detailing": questions[14:19],
        "Monitoring, Evaluation & Reporting (MER)": questions[19:24]
    }

    # Gemini prompt
    prompt = """
You are provided the text of a scored Climate Action questionnaire.
Please extract the score assigned to each of the following 24 sub-questions, labeled as:

1.1 to 1.7 - Energy Emissions Inventory  
2.1 to 2.7 - Strategy Identification  
3.1 to 3.6 - Action Prioritization & Detailing  
4.1 to 4.5 - Monitoring, Evaluation & Reporting (MER)

Respond in this exact format:

Community Name: <Name>
1.1: <score>
1.2: <score>
...
4.5: <score>

Do not skip any labels. Keep each on a new line.
"""

    model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")
    input_folder = Path(folder_path)
    analysis_files = list(input_folder.glob("*_analysis.docx"))

    if not analysis_files:
        print("No DOCX files found.")
        return

    for docx_path in analysis_files:
        try:
            doc = Document(docx_path)
            full_text = "\n".join(p.text for p in doc.paragraphs)

            response = model.generate_content([prompt, full_text])
            text = response.text

            data = {}

            # Extract Community Name
            name_match = re.search(r"Community Name:\s*(.+)", text)
            community_name = name_match.group(1).strip() if name_match else docx_path.stem
            data["Community Name"] = community_name
            data["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            total_score = 0

            # Extract all 24 scores
            for q in questions:
                match = re.search(rf"{q}:\s*(\d+)", text)
                score = int(match.group(1)) if match else 0
                data[q] = score
                total_score += score

            # Add category totals
            for category, q_list in categories.items():
                data[category] = sum(data[q] for q in q_list)

            data["Total Score"] = total_score

            # Create DataFrame
            df_single = pd.DataFrame([data])

            # Define output path
            safe_name = re.sub(r'[\\/*?:"<>|]', "_", community_name)
            output_path = input_folder / f"{safe_name}_scoring.xlsx"

            # Append to existing file if it exists
            if output_path.exists():
                existing_df = pd.read_excel(output_path)
                combined_df = pd.concat([existing_df, df_single], ignore_index=True)
            else:
                combined_df = df_single

            # Save updated file
            combined_df.to_excel(output_path, index=False)
            print(f"✅ Saved/updated: {output_path}")

        except Exception as e:
            print(f"❌ Error processing {docx_path.name}: {e}")

# --- Run it ---
if __name__ == "__main__":
    folder_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/analysis_output/Excel_scoring/iteration2"
    api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"  # Replace with your actual Gemini API key
    analyze_questionnaire_reports(folder_input, api_key)