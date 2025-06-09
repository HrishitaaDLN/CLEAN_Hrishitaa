import google.generativeai as genai
from pathlib import Path
import time
import pandas as pd
import os
import re
import json

def getScores(api_key: str, folder_path: str) -> None:
    """
    Processes sustainability PDFs using Gemini, extracts JSON, saves both JSON and Excel output per document.
    """
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured.")
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return

    folder = Path(folder_path.strip())
    if not folder.is_dir():
        print(f"❌ Folder not found: {folder}")
        return

    output_folder = folder / "analysis_output_excel"
    output_folder.mkdir(exist_ok=True)
    print(f"📁 Output folder: {output_folder.resolve()}")

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ No PDF files found in folder.")
        return

       # 7. Define the analysis prompt
    prompt = """
You are provided with city sustainability reports (Climate Action Plans or similar documents).

Task Instructions:
✅ Step 1: Identify and Extract Stationary Energy Actions
• Review each report carefully.
• List stationary energy actions explicitly described, clearly using a "verb + object" format (e.g., "Install solar panels," "Retrofit municipal buildings").

✅ Step 2: Categorize Actions
• Assign each identified action explicitly to exactly one of these categories aligned with the GHG Protocol for Cities (GPC):
  o Solar Energy
  o Wind Energy
  o Geothermal
  o EV Infrastructure
  o Battery Storage
  o Building Retrofits
  o Lighting Efficiency
  o Energy Codes & Policy
  o Community Engagement
  o Grid Resilience
  o Other Energy Actions (specify clearly)

✅ Step 3: Provide Evidence
• For each action and emissions inventory value, provide explicit evidence from the report (direct quote, document name, page number).

✅ Step 4: Structure the Summary Table
• Organize results into an Excel file named:
  Clustered_Energy_Actions_and_Emissions.xlsx
• Use this exact structure:
Category | Action Description | Document Name | Page Number(s) | Village Name | Report Date

✅ Step 5: Clearly State if No Actions Identified
• If no stationary energy actions are explicitly identified in a document, clearly state:
  "No stationary energy actions identified in this report."

✅ Step 6: Clearly State if No Inventory Values Identified
• If no stationary energy emissions inventory values are explicitly identified in a document, clearly state:
  "No stationary energy emissions inventory values identified in this report."

✅ Step 7: Summarize Findings
• At the end of the Excel file, briefly summarize (2–3 sentences) the most common stationary energy actions identified and common trends observed in emissions inventory reporting across the reviewed documents.

✅ Output JSON in this structure:

[
  {
    "Category": "Lighting Efficiency",
    "Action Description": "Replace incandescent bulbs with LEDs",
    "Document Name": "City_Report.pdf",
    "Page Number(s)": "12",
    "Village Name": "Aurora",
    "Report Date": "2021-06-01",
    "Evidence for Action": "Page 12: The city replaced traffic signals with LED lights to reduce power usage."
  }
]

✅ If no actions, return: [{"note": "No stationary energy actions identified"}]  
✅ If no inventory values, return: [{"note": "No stationary energy emissions inventory values identified"}]

"""

    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-03-25")

    for pdf_path in pdf_files:
        print(f"\n📄 Processing: {pdf_path.name}")
        pdf_file = None

        try:
            pdf_file = genai.upload_file(path=pdf_path)
            print(f"✅ Uploaded: {pdf_file.name}")

            while pdf_file.state.name == "PROCESSING":
                time.sleep(5)
                pdf_file = genai.get_file(name=pdf_file.name)

            if pdf_file.state.name != "ACTIVE":
                print(f"❌ File not active. Skipping: {pdf_path.name}")
                continue

            response = model.generate_content([prompt, pdf_file])
            raw_text = response.text.strip()

            # Extract first valid JSON array block
            match = re.search(r"\[\s*{.*?}\s*\]", raw_text, re.DOTALL)
            if not match:
                print("⚠️ No structured JSON found.")
                raw_out = output_folder / f"{pdf_path.stem}_RAW.txt"
                with open(raw_out, "w", encoding="utf-8") as f:
                    f.write(raw_text)
                print(f"📄 Saved raw output: {raw_out.name}")
                continue

            json_text = match.group(0)

            try:
                data = json.loads(json_text)

                # Save JSON
                json_file = output_folder / f"{pdf_path.stem}_energy_actions.json"
                with open(json_file, "w", encoding="utf-8") as jf:
                    json.dump(data, jf, indent=2)
                print(f"📦 Saved JSON: {json_file.name}")

                # Convert to Excel
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    excel_file = output_folder / f"{pdf_path.stem}_energy_actions.xlsx"
                    df.to_excel(excel_file, index=False)
                    print(f"📊 Saved Excel: {excel_file.name}")
                else:
                    print("⚠️ JSON structure not suitable for tabular output.")

            except Exception as e:
                print(f"❌ JSON parsing error: {e}")
                fallback = output_folder / f"{pdf_path.stem}_RAW.txt"
                with open(fallback, "w", encoding="utf-8") as f:
                    f.write(raw_text)
                print(f"📄 Raw fallback saved: {fallback.name}")

        except Exception as e:
            print(df)
            print(f"❌ Error with file '{pdf_path.name}': {e}")

        finally:
            if pdf_file and hasattr(pdf_file, 'name'):
                try:
                    genai.delete_file(name=pdf_file.name)
                    print(f"🗑️ Deleted Gemini file: {pdf_file.name}")
                except Exception as cleanup_error:
                    print(f"⚠️ File cleanup error: {cleanup_error}")

# --- Script Entry ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"
    folder_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActions"

    if my_api_key:
        print("🚀 Starting batch analysis...")
        getScores(my_api_key, folder_path_input)
        print("✅ Done.")
    else:
        print("❌ No API key provided.")
