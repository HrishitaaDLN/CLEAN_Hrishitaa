import google.generativeai as genai
from pathlib import Path
import time
import pandas as pd
import json
import re
import datetime

def extract_prioritized_actions(api_key: str, folder_path: str) -> None:
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured.")
    folder = Path(folder_path.strip())
    output_folder = folder / "prioritized_action_output"
    output_folder.mkdir(exist_ok=True)

    pdf_files = list(folder.glob("*.pdf"))
    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-03-25")
    all_data = []

    prompt_template = """
You are provided with city sustainability reports (Climate Action Plans or similar documents).
Your task is to extract **action prioritization strategies** related to:
- Stationary Energy
- Waste
- Transport

Focus on **how cities prioritize, rank, or sequence their actions**, including:
- Time-phased plans (e.g., short/medium/long-term)
- Priority tiers (e.g., high/low/phase 1)
- Criteria (e.g., cost-effectiveness, equity)

✅ For each prioritized action, example, return:
[
  {
    "Sector": "Stationary Energy",
    "Action Description": "Retrofit municipal buildings for energy efficiency",
    "Priority Level": "High",
    "Criteria": "GHG reduction, feasibility",
    "Page Number(s)": "10, 14",
    "Evidence": "The City prioritized retrofits due to energy savings potential.",
    "Document Name": "Green Town: The City of Waukegan Sustainability Plan.pdf",
    "Village Name": "Extracted from the document's title or text (e.g., 'City of Waukegan')",
    "Report Date": "Extracted from document (e.g., '2023')"
  }
]

✅ Be sure to extract **Village Name** and **Report Date** from the document text itself. Do not infer or fabricate.

✅ If no prioritization info found, return:
[
  { "note": "No prioritization of stationary energy, waste, or transport actions found in this document." }
]

✅ Also add at the end:
Summary:

Total prioritized actions found: X  
Stationary Energy: Y (P%)  
Waste: Z (Q%)  
Transport: W (R%)
"""

    for pdf_path in pdf_files:
        try:
            pdf_file = genai.upload_file(path=pdf_path)
            while pdf_file.state.name == "PROCESSING":
                time.sleep(5)
                pdf_file = genai.get_file(name=pdf_file.name)
            print(f"\n📄 Processing: {pdf_path.name}")

            if pdf_file.state.name != "ACTIVE":
                continue

            response = model.generate_content([prompt_template, pdf_file])
            raw_text = response.text.strip()

            json_match = re.search(r"\[\s*{.*?}\s*\]", raw_text, re.DOTALL)
            if json_match:
                json_block = json_match.group(0)
                try:
                    extracted = json.loads(json_block)
                    for item in extracted:
                        if "Sector" in item:
                            item["Document Name"] = item.get("Document Name", pdf_path.name)
                            all_data.append(item)
                except Exception as e:
                    print(f"❌ JSON decode error: {e}")

            genai.delete_file(name=pdf_file.name)

        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")

    if all_data:
        df = pd.DataFrame(all_data)
        df["Sector"] = df["Sector"].str.title()

        # Summary
        sector_summary = df["Sector"].value_counts().reset_index()
        sector_summary.columns = ["Sector", "Count"]
        sector_summary["Percentage"] = (sector_summary["Count"] / sector_summary["Count"].sum() * 100).round(2)

        # Save to Excel
        output_excel = output_folder / "Prioritized_Actions_and_Summary.xlsx"
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Prioritized Actions", index=False)
            sector_summary.to_excel(writer, sheet_name="Summary", index=False)

        print(f"\n✅ Excel saved: {output_excel.resolve()}")
    else:
        print("\n⚠️ No prioritized actions extracted from any PDFs.")


def extract_village_name(filename_stem):
    # Try to clean up name to guess village name
    words = re.split(r'[_\-\.]', filename_stem)
    likely_name = " ".join(word for word in words if word.lower() not in {"climate", "action", "plan", "sustainability", "ghg", "final", "report", "environmental"})
    return likely_name.strip().title()

# --- Run the script ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"
    folder_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActionPrioritization"

    extract_prioritized_actions(my_api_key, folder_path_input)