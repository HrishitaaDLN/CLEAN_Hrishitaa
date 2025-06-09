import google.generativeai as genai
from pathlib import Path
import pandas as pd
import json
import re
import time

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
You are analyzing a dataset of sustainability actions. Each entry includes:
- "Action Description": A text describing an energy or environmental action.
- "Village Name": The city or municipality associated with the action.

Your job is to:
1. Extract and group the **repeated types of actions**.
2. Identify the **associated village(s)** for each type of action.
3. **Cluster** each action into one of the following categories:
   - Solar Energy
   - Wind Energy
   - Geothermal
   - EV Infrastructure
   - Battery Storage
   - Building Retrofits
   - Lighting Efficiency
   - Energy Codes & Policy
   - Community Engagement
   - Grid Resilience
   - Other Energy Actions (specify clearly what the action is about)

4. For each action, return:
   - A representative **action** string (canonical name).
   - A list of **villages**.
   - The assigned **category**.
   - A **justification** of why this action fits the category.

Use this JSON format:
[
  {{
    "action": "Add 2,000 MW of renewable generation",
    "villages": ["Algonquin Power & Utilities Corp."],
    "category": "Solar Energy",
    "justification": "The action refers to renewable energy and aligns with typical solar development by utilities."
  }}
]
Rules:

Group similar phrases (e.g., “install solar panels”, “develop solar farm”) under one canonical action.

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
    excel_path_input = "d:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractActionPrioritization/MostCommonPrioritisedActions/Prioritized_Actions_and_Summary_final.xlsx"  # <-- CHANGE THIS

    print("🚀 Starting Gemini Excel clustering analysis...")
    analyze_excel_actions(my_api_key, excel_path_input)
    print("✅ Done.")
