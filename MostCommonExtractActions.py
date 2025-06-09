import google.generativeai as genai
from pathlib import Path
import pandas as pd
import json
import re

def analyze_excel_actions(api_key: str, excel_path: str) -> None:
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured.")
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return

    file = Path(excel_path.strip())
    if not file.is_file() or not file.name.endswith(".xlsx"):
        print(f"❌ Excel file not found: {file}")
        return

    output_folder = file.parent / "analysis_output_excel"
    output_folder.mkdir(exist_ok=True)
    print(f"📁 Output folder: {output_folder.resolve()}")

    try:
        df = pd.read_excel(file)
        if "Action Description" not in df.columns or "Village Name" not in df.columns:
            print("❌ Required columns not found in Excel.")
            return
        print(f"📄 Loaded file: {file.name}, Rows: {len(df)}")
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # Prepare data as a string
    action_data = df[['Action Description', 'Village Name']].dropna().to_dict(orient='records')
    text_data = "\n".join([f"Action: {row['Action Description']}\nVillage: {row['Village Name']}" for row in action_data])

    # Gemini prompt
    prompt = f"""
You are given one or more Excel files. Each file contains a list of sustainability-related actions taken by different villages.

Each row in the Excel file includes at least the following columns:
- "Action Description"
- "Village Name"
- "Category" (e.g., Solar Energy, Building Retrofits, etc.)

Your task is to:
1. Go through **all rows** in the Excel data.
2. Identify **repeated or similar actions** based on the "Action Description".
3. For each group of similar actions:
   - Provide a **representative action name**
   - List all associated **village names**
   - Include the most appropriate **category** based on context

Return your output as a structured **JSON list** like this:

```json
[
  {{
    "action": "Install solar panels",
    "villages": ["City of Aurora", "Village of Skokie", "City of Naperville"],
    "category": "Solar Energy"
  }},
  {{
    "action": "Upgrade building insulation",
    "villages": ["City of Aurora", "Village of Oak Park"],
    "category": "Building Retrofits"
  }}
]
Analyze this data and return the JSON:
{text_data}
"""
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")
    response = model.generate_content(prompt)
    raw_text = response.text.strip()

    # Extract first valid JSON array block
    match = re.search(r"\[\s*{.*?}\s*\]", raw_text, re.DOTALL)
    if not match:
        print("⚠️ No structured JSON found.")
        raw_out = output_folder / f"{file.stem}_RAW.txt"
        with open(raw_out, "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"📄 Saved raw output: {raw_out.name}")
        return

    json_text = match.group(0)

    try:
        data = json.loads(json_text)

        # Save JSON
        json_file = output_folder / f"{file.stem}_clustered_actions.json"
        with open(json_file, "w", encoding="utf-8") as jf:
            json.dump(data, jf, indent=2)
        print(f"📦 Saved JSON: {json_file.name}")

        # Save Excel
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df_out = pd.DataFrame(data)
            excel_file = output_folder / f"{file.stem}_clustered_actions.xlsx"
            df_out.to_excel(excel_file, index=False)
            print(f"📊 Saved Excel: {excel_file.name}")
        else:
            print("⚠️ JSON structure not suitable for tabular output.")

    except Exception as e:
        print(f"❌ JSON parsing error: {e}")
        fallback = output_folder / f"{file.stem}_RAW.txt"
        with open(fallback, "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"📄 Raw fallback saved: {fallback.name}")

# --- Entry Point ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"  # Replace with your actual key securely
    excel_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActions/analysis_output_excel/Analyse/merged_output.xlsx"  # <-- CHANGE THIS

    print("🚀 Starting Gemini Excel clustering analysis...")
    analyze_excel_actions(my_api_key, excel_path_input)
    print("✅ Done.")
