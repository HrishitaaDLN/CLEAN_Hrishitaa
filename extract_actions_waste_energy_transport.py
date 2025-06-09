import google.generativeai as genai
from pathlib import Path
import time
import pandas as pd
import json
import re

def extract_actions_and_categorize(api_key: str, folder_path: str) -> None:
    """
    Processes all PDF files in the specified folder, extracts and categorizes actions related to
    Stationary Energy, Waste, and Transport using Gemini, and saves the results in an Excel file.
    Also extracts Village Name and Report Date if explicitly mentioned.
    """
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured.")
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return

    folder = Path(folder_path.strip())
    if not folder.is_dir():
        print(f"❌ Folder not found at '{folder_path}'")
        return

    output_folder = folder / "action_output"
    output_folder.mkdir(exist_ok=True)
    print(f"📁 Output folder ready: {output_folder.resolve()}")

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ No PDF files found in the specified folder.")
        return

    # Enhanced Prompt
    prompt_template = """
You are provided with city sustainability reports (Climate Action Plans or similar documents).
Your task is to:
1. Extract specific actions related to Stationary Energy, Waste, and Transport in the report.
2. Categorize each action as one of the following:
   - Stationary Energy
   - Waste
   - Transport
3. Extract the Village Name (e.g., city, town, or village name) and Report Date explicitly from the document.

✅ Return your output in valid JSON format only — a list of dictionaries like this:
[
  {
    "action": "Retrofitting municipal buildings for energy efficiency",
    "category": "Stationary Energy",
    "village_name": "City of Aurora",
    "report_date": "2023"
  },
  ...
]

🚫 Do not include markdown, explanations, or inferred data. Only extract what is explicitly stated in the document.
🚫 If Village Name or Report Date are not found, leave them as empty strings.
"""

    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-03-25")
    all_actions = []

    for pdf_path in pdf_files:
        print(f"\n📄 Processing '{pdf_path.name}'...")
        pdf_file = None

        try:
            pdf_file = genai.upload_file(path=pdf_path)
            print(f"✅ Uploaded as file ID: {pdf_file.name}")

            # Wait for file to process
            while pdf_file.state.name == "PROCESSING":
                time.sleep(5)
                pdf_file = genai.get_file(name=pdf_file.name)
                print(f"⏳ Waiting... File state: {pdf_file.state.name}")

            if pdf_file.state.name != "ACTIVE":
                print("❌ File not active. Skipping.")
                continue

            print("🤖 Sending to Gemini...")
            response = model.generate_content([prompt_template, pdf_file])
            raw_text = response.text.strip()

            # --- Parse JSON block using regex ---
            json_match = re.search(r"\[\s*{.*?}\s*\]", raw_text, re.DOTALL)
            if json_match:
                json_block = json_match.group(0)
                try:
                    extracted = json.loads(json_block)
                    for item in extracted:
                        action = item.get("action", "").strip()
                        category = item.get("category", "").strip().title()
                        village_name = item.get("village_name", "").strip()
                        report_date = item.get("report_date", "").strip()

                        if action:
                            all_actions.append({
                                "Action": action,
                                "Category": category,
                                "Village Name": village_name,
                                "Report Date": report_date,
                                "Source PDF": pdf_path.name
                            })
                    print(f"✅ Parsed {len(extracted)} actions from '{pdf_path.name}'.")
                except Exception as e:
                    print(f"❌ JSON parse error: {e}")
                    print("🔎 JSON block:\n", json_block)
            else:
                print("❌ No JSON block found.")
                debug_file = output_folder / f"{pdf_path.stem}_gemini_raw.txt"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(raw_text)
                print(f"📝 Saved raw Gemini output to: {debug_file}")

            # Always delete the file after processing
            genai.delete_file(name=pdf_file.name)

        except Exception as e:
            print(f"❌ Error processing '{pdf_path.name}': {e}")
            if pdf_file and hasattr(pdf_file, 'name'):
                try:
                    genai.delete_file(name=pdf_file.name)
                    print(f"🗑️ Cleaned up Gemini file: {pdf_file.name}")
                except:
                    pass

    # --- Save Final Output ---
    if all_actions:
        print(f"\n🧾 Total actions extracted: {len(all_actions)}")
        df = pd.DataFrame(all_actions, columns=[
            "Action", "Category", "Village Name", "Report Date", "Source PDF"
        ])

        df["Category"] = df["Category"].where(
            df["Category"].isin(["Stationary Energy", "Waste", "Transport"]),
            "Other"
        )

        # Summary table
        summary = df["Category"].value_counts().reset_index()
        summary.columns = ["Category", "Count"]
        summary["Percentage"] = (summary["Count"] / summary["Count"].sum() * 100).round(2)

        output_excel = output_folder / "Extracted_Actions_Summary.xlsx"
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="All Actions", index=False)
            summary.to_excel(writer, sheet_name="Summary", index=False)

        print(f"\n✅ Excel saved to:\n{output_excel.resolve()}")
    else:
        print("\n⚠️ No actions extracted from any PDFs. No Excel created.")

# --- Example usage ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"  # Replace with your actual Gemini API key
    folder_path_input = "D:/All Municipality Reports/Final_Municipality_Reports_For_Analysis/ExtractEnergyWasteTransport"

    if my_api_key:
        print("\n🚀 Starting action extraction...")
        extract_actions_and_categorize(my_api_key, folder_path_input)
        print("\n🏁 Extraction process completed.")
    else:
        print("❌ API Key is missing. Please provide a valid Gemini API key.")
