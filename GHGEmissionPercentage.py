import google.generativeai as genai
from pathlib import Path
import time
import pandas as pd
import json
import re

def extract_ghg_percentages(api_key: str, folder_path: str) -> None:
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured.")
    folder = Path(folder_path.strip())
    output_folder = folder / "ghg_sector_output"
    output_folder.mkdir(exist_ok=True)

    pdf_files = list(folder.glob("*.pdf"))
    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-03-25")
    all_data = []

    prompt_template = """
You are given a city’s Climate Action Plan or GHG inventory report.

🎯 Your task:
Extract the **percentage of total GHG emissions** that come from each of the following sectors:
- **Stationary Energy**
- **Waste**
- **Transport**

📋 For each sector, return:

1. **% of Total GHG Emissions**
2. **Numerator and Denominator (if available)** – e.g., 135,000 tCO₂e / 300,000 tCO₂e
3. **Units used**
4. **Scope(s) included**
5. **Justification / Source Text** – include page number(s) or section reference
6. **Document Name**
7. **Village or City Name**
8. **Report Date (if mentioned in the text or metadata)**

Output format:
```json
[
  {
    "Sector": "Stationary Energy",
    "Percentage GHG": 45,
    "Sector Emissions": "135,000 tCO₂e",
    "Total Emissions": "300,000 tCO₂e",
    "Units": "tCO₂e",
    "Scopes": "Scope 1 and 2",
    "Justification": "On page 10: 'In 2022, stationary energy accounted for 135,000 tCO₂e out of 300,000 tCO₂e total emissions.'",
    "Document Name": "Village_of_Lincolnwood_Sustainability_Plan_2023.pdf",
    "Village Name": "Lincolnwood",
    "Report Date": "2023"
  },
  ...
]
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

        output_excel = output_folder / "GHG_By_Sector_Extracted.xlsx"
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="GHG Sector Breakdown", index=False)

            # Optional: Create pivot for percentage comparison
            pivot = df.pivot_table(
                index="Document Name",
                columns="Sector",
                values="Percentage GHG",
                aggfunc="first"
            ).reset_index()
            pivot.to_excel(writer, sheet_name="Summary Table", index=False)

        print(f"\n✅ Excel saved to: {output_excel.resolve()}")
    else:
        print("\n⚠️ No GHG breakdown data extracted.")

# --- Run the script ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"
    folder_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/GHGEmissionPercentage"

    extract_ghg_percentages(my_api_key, folder_path_input)
