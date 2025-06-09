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
• Extract explicitly reported stationary energy emissions inventory values according to GHG Protocol scopes:
  o Scope 1: On-site fuel combustion  
  o Scope 2: Grid-supplied electricity, heat, or steam  
  o Scope 3: Upstream or downstream stationary energy emissions (if explicitly reported)  

• Clearly state units used for each scope (e.g., metric tonnes CO₂e [tCO₂e], megawatt-hours [MWh]).

• Explicitly record the evidence of:
  - Scope 1 Emissions, Scope 1 Units  
  - Scope 2 Emissions, Scope 2 Units  
  - Scope 3 Emissions, Scope 3 Units  
  - Total Emissions and Total Units  

• ⚠️ Additionally, extract and include:
  - **Village Name** (name of the city/town/village)  
  - **Report Date** (year or full date if available from the report or metadata)  

The summary table should look like:

Village Name | Report Date | Document Name | Scope 1 Emissions | Evidence for Scope 1 Emissions | Scope 1 Units | Evidence for Scope 1 Units | Scope 2 Emissions | Evidence for Scope 2 Emissions | Scope 2 Units | Evidence for Scope 2 Units | Scope 3 Emissions | Evidence for Scope 3 Emissions | Scope 3 Units | Evidence for Scope 3 Units | Total Stationary Emissions | Total Units

Output JSON in this structure:  

[
  {
    "Village Name": "Aurora",
    "Report Date": "2021-05-01",
    "Document Name": "Aurora_Sustainability_Report.pdf",
    "Scope 1 Emissions": "3200",
    "Evidence for Scope 1 Emissions": "Page 12: Scope 1 emissions were estimated at 3200 tCO₂e from onsite fuel usage.",
    "Scope 1 Units": "tCO2e",
    "Evidence for Scope 1 Units": "Page 12: Emissions reported in metric tonnes CO2 equivalent.",
    "Scope 2 Emissions": "4800",
    "Evidence for Scope 2 Emissions": "Page 13: Grid-based electricity resulted in 4800 tCO2e.",
    "Scope 2 Units": "tCO2e",
    "Evidence for Scope 2 Units": "Page 13: Grid electricity measured in tCO2e.",
    "Scope 3 Emissions": "1200",
    "Evidence for Scope 3 Emissions": "Page 15: Scope 3 emissions include purchased goods and services.",
    "Scope 3 Units": "tCO2e",
    "Evidence for Scope 3 Units": "Page 15: Report uses tCO2e for all indirect emissions.",
    "Total Stationary Emissions": "9200",
    "Total Units": "tCO2e"
  }
]
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
                json_file = output_folder / f"{pdf_path.stem}_scope123_emissions.json"
                with open(json_file, "w", encoding="utf-8") as jf:
                    json.dump(data, jf, indent=2)
                print(f"📦 Saved JSON: {json_file.name}")

                # Convert to Excel
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    excel_file = output_folder / f"{pdf_path.stem}_scope123_emissions.xlsx"
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
    folder_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/Scope123Emissions"

    if my_api_key:
        print("🚀 Starting batch analysis...")
        getScores(my_api_key, folder_path_input)
        print("✅ Done.")
    else:
        print("❌ No API key provided.")
