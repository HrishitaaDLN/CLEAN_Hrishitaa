import google.generativeai as genai
from pathlib import Path
import time
import pandas as pd

# --- Function Definition ---
def cluster_energy_actions(api_key: str, folder_path: str) -> None:
    """
    Processes all PDF files in the specified folder, clusters stationary energy actions using Gemini,
    and saves the results in an Excel file.
    """
    try:
        genai.configure(api_key=api_key)
        print("Gemini API configured.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    folder = Path(folder_path.strip())
    if not folder.is_dir():
        print(f"Error: Folder not found at '{folder_path}'")
        return

    output_folder = Path(folder) / "clustered_output"
    output_folder.mkdir(exist_ok=True)
    print(f"Created/accessed output folder: {output_folder}")

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return

    prompt = """
You are provided with a set of documents containing extracted stationary energy actions (in verb + object format) from various Climate Action Plan reports.

Your task is to:
✅ Read through each document.
✅ For each extracted action, assign it to one of the following categories:
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
- Other Energy Actions

✅ Create a summary table with columns:
| Category | Action | Document Name | Page Number(s) |

✅ If no actions are found in a document, state:
"No stationary energy actions identified in this report."

✅ At the end, provide a brief summary describing the most common types of actions identified across reports.

✅ Format the results in an Excel file named 'Clustered_Energy_Actions.xlsx'.
"""

    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-03-25")

    all_data = []

    for pdf_path in pdf_files:
        print(f"\nProcessing '{pdf_path.name}'...")
        pdf_file = None

        try:
            pdf_file = genai.upload_file(path=pdf_path)
            print(f"Successfully uploaded '{pdf_path.name}' as file ID: {pdf_file.name}")

            while pdf_file.state.name == "PROCESSING":
                time.sleep(5)
                pdf_file = genai.get_file(name=pdf_file.name)
                print(f"Current file state: {pdf_file.state.name}")

            if pdf_file.state.name != "ACTIVE":
                print(f"Error: File processing failed or file is not active.")
                continue

            print("File processed. Sending request for analysis...")

            response = model.generate_content([prompt, pdf_file])

            if response.text:
                # Parse response for table extraction
                lines = response.text.strip().split('\n')
                for line in lines:
                    if "|" in line and not line.startswith("| Category"):
                        parts = [part.strip() for part in line.split("|")[1:-1]]
                        if len(parts) == 4:
                            all_data.append(parts + [pdf_path.name])

            genai.delete_file(name=pdf_file.name)
            print(f"Deleted file {pdf_file.name} from Gemini server.")

        except Exception as e:
            print(f"An error occurred: {e}")
            if pdf_file and hasattr(pdf_file, 'name'):
                try:
                    genai.delete_file(name=pdf_file.name)
                    print(f"Deleted file {pdf_file.name} after error.")
                except:
                    pass

    if all_data:
        df = pd.DataFrame(all_data, columns=["Category", "Action", "Document Name", "Page Numbers", "Source PDF"])
        output_excel = output_folder / "Clustered_Energy_Actions.xlsx"
        df.to_excel(output_excel, index=False)
        print(f"Excel summary saved to: {output_excel}")
    else:
        print("No valid data found to generate Excel.")

# --- Example Usage ---
if __name__ == "__main__":
    my_api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"
    folder_path_input = "D:/All Municipality Reports_selected_50_analysis/analysis_output/pdfs"

    if my_api_key:
        print("\nStarting clustering process...")
        cluster_energy_actions(my_api_key, folder_path_input)
        print("\nClustering process completed.")
    else:
        print("API Key is missing. Please provide a valid Gemini API key.")
