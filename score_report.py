from docx import Document
from pathlib import Path
import pandas as pd
import re
import google.generativeai as genai

def analyze_gpc_scores(folder_path: str, api_key: str) -> pd.DataFrame:
    """
    Extracts climate scoring info from analysis .docx files using Gemini and your custom GPC-based prompt.

    Args:
        folder_path (str): Path to the folder containing *_analysis.docx files.
        api_key (str): Gemini API key.

    Returns:
        pd.DataFrame: Scores by category + total per document.
    """
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")

    categories = {
        "Emissions Inventory": 6,
        "Strategy Identification": 7,
        "Action Prioritization & Detailing": 5,
        "Monitoring, Evaluation & Reporting (MER)": 5,
    }

    scoring_prompt = """
You are provided with a city's official Climate Action Plan (CAP) or similar official planning document. Your task is to assess the city's maturity in managing stationary energy emissions according to the Global Protocol for Community-Scale Greenhouse Gas Emission Inventories (GPC).
Answer the 23 yes/no questions exactly and assign 1 point for "Yes", 0 for "No".
Respond in this exact format:

Community Name: <name>

Section 1 (Emissions Inventory): X / 6  
Section 2 (Strategy Identification): X / 7  
Section 3 (Action Prioritization & Detailing): X / 5  
Section 4 (Monitoring, Evaluation & Reporting (MER)): X / 5
"""

    input_folder = Path(folder_path)
    analysis_files = list(input_folder.glob("*_analysis.docx"))

    results = []
    for docx_path in analysis_files:
        try:
            doc = Document(docx_path)
            full_text = "\n".join(p.text for p in doc.paragraphs)

            print(f"📄 Analyzing: {docx_path.name}")
            response = model.generate_content([scoring_prompt, full_text])
            if not response.text:
                continue

            text = response.text
            data = {
                "Document": docx_path.name,
                "Community Name": re.search(r"Community Name:\s*(.+)", text).group(1).strip()
                if re.search(r"Community Name:\s*(.+)", text)
                else "Unknown"
            }

            total_score = 0
            max_score = 0

            for idx, (cat, max_val) in enumerate(categories.items(), start=1):
                pattern = rf"Section {idx} \({re.escape(cat)}\):\s*(\d+)\s*/\s*(\d+)"
                match = re.search(pattern, text)
                score = int(match.group(1)) if match else 0
                data[cat] = score
                total_score += score
                max_score += max_val

            data["Total Score"] = total_score
            data["Max Score"] = max_score
            data["Fraction"] = round(total_score / max_score, 2) if max_score > 0 else 0
            results.append(data)

        except Exception as e:
            print(f"❌ Error processing {docx_path.name}: {e}")

    df = pd.DataFrame(results)
    if not df.empty:
        cols = ["Document", "Community Name"] + list(categories.keys()) + ["Total Score", "Max Score", "Fraction"]
        df = df[cols]
    return df

# ----------- Run this block -------------
if __name__ == "__main__":
    folder_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/analysis_output"
    api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"

    df = analyze_gpc_scores(folder_input, api_key)
    output_path = f"{folder_input}/gpc_scored_reports.csv"
    df.to_csv(output_path, index=False)
    print(f"✅ GPC scoring completed. Saved to: {output_path}")