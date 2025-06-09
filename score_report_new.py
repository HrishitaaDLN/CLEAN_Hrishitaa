from docx import Document
from pathlib import Path
import pandas as pd
import re

import google.generativeai as genai
from pathlib import Path
import pandas as pd
from docx import Document
import re

def analyze_scored_reports_with_gemini(folder_path: str, api_key: str) -> pd.DataFrame:
    """
    Sends each *_analysis.docx file to Gemini and extracts scoring data from the text
    based on the standard 8-category climate action evaluation.

    Args:
        folder_path: Path to folder containing *_analysis.docx files.
        api_key: Google Gemini API key.

    Returns:
        DataFrame with extracted scores per report.
    """
    genai.configure(api_key=api_key)

    categories = {
        "First Steps": 2,
        "Governance": 1,
        "Stakeholder & Community Engagement": 7,
        "GHG Emissions Inventory": 4,
        "Sustainability Risk Assessment": 8,
        "City Needs Assessment": 3,
        "Strategy Identification": 10,
        "Action Prioritization & Detailing": 6,
        "Equity & Inclusivity": 7,
        "Monitoring, Evaluation & Reporting (MER)": 7,
    }

    prompt = """
    You are provided the text of a scored Climate Action Plan or related analysis report.
    Extract the numeric scores for each of the 10 standard categories below based on the provided report content.

    Use this format strictly in your response:
    Community Name: <Name>
    Section 1 (First Steps): X / 2
    Section 2 (Governance): X / 1
    Section 3 (Stakeholder & Community Engagement): X / 6
    Section 4 (GHG Emissions Inventory): X / 3
    Section 5 (Sustainability Risk Assessment): X / 7
    Section 6 (City Needs Assessment): X / 2
    Section 7 (Strategy Identification): X / 9
    Section 8 (Action Prioritization & Detailing): X / 5
    Section 9 (Equity & Inclusivity): X / 6
    Section 10 (Monitoring, Evaluation & Reporting (MER)): X / 7
    """

    model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")
    input_folder = Path(folder_path)
    analysis_files = list(input_folder.glob("*_analysis.docx"))

    # Initialize DataFrame with all expected columns
    df = pd.DataFrame(columns=["Community Name"] + list(categories.keys()) + ["Total Score", "Fraction"])

    for docx_path in analysis_files:
        try:
            doc = Document(docx_path)
            full_text = "\n".join(p.text for p in doc.paragraphs)
            print(f"Extracted text from {docx_path.name}: {full_text[:100]}...")  # Print first 100 characters of extracted text
            response = model.generate_content([prompt, full_text])
            print(f"Model response: {response.text}")  # Print model response
            if not response.text:
                print(f"No response from model for {docx_path.name}")
                continue

            text = response.text
            data = {"Community Name": re.search(r"Community Name: (.+)", text).group(1).strip() if re.search(r"Community Name: (.+)", text) else "Unknown"}
            total_score = 0
            max_score = 0
            for idx, (cat, max_val) in enumerate(categories.items(), start=1):
                pattern = rf"Section {idx} \({re.escape(cat)}\): (\d+) / (\d+)"
                match = re.search(pattern, text)
                if match:
                    val = int(match.group(1))
                    print(f"Extracted score for {cat} in {data['Community Name']}: {val}")
                else:
                    val = 0
                    print(f"WARNING: No score found for section '{cat}' in {data['Community Name']} (Section {idx})")
                data[cat] = val
                total_score += val
                max_score += max_val

            data["Total Score"] = total_score
            data["Fraction"] = round(total_score / max_score, 2) if max_score > 0 else 0
            if total_score == 0:
                print(f"WARNING: Total score is zero for {data['Community Name']}. Check extraction and model response.")
            df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
        except Exception as e:
            print(f"Error processing {docx_path.name}: {e}")

    return df

if __name__ == "__main__":
    folder_input =  "/Users/satendergunwal/Desktop/CGithub-SGunwal/CLEAN/sustainable_maturity_mapping/single_test_report/analysis_output_3"
    #"community_reports/GRC_Reports/analysis_output"  #input("Enter path to folder containing *_analysis.docx files: ").strip()
    api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY" #input("Enter your Gemini API key: ").strip()
    df = analyze_scored_reports_with_gemini(folder_input, api_key)
    # print(df.to_string(index=False))
    df.to_csv(f"{folder_input}/scored_reports.csv", index=False)
    print(f"Scored reports saved to {folder_input}/scored_reports.csv")

