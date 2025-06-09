import google.generativeai as genai
import pandas as pd
from pathlib import Path
import time
import os

# Configure Gemini API
def classify_actions_with_gemini(api_key, input_excel, output_excel):
    try:
        genai.configure(api_key=api_key)
        print(" Gemini API configured.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    # Load the Excel file
    df = pd.read_excel(input_excel)
    if 'Action' not in df.columns:
        print(" No 'Action' column found in Excel.")
        return

    # Prepare prompt for each action
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

    stakeholder_list = []
    justification_list = []
    print(" Classifying actions...")

    for idx, action in enumerate(df['Action']):
        if pd.isna(action):
            stakeholder_list.append("Other")
            justification_list.append("No action provided.")
            continue
        print(justification_list)
        prompt = f"""
You are an expert in climate action analysis.

For the following energy/climate action, determine who the primary stakeholder or beneficiary is. Return exactly two things:
A stakeholder group label (one clear category from Municipality, Residents, Businesses.).
A brief justification (1-2 sentences) explaining why you assigned that stakeholder group.

Action: "{action}", "{justification_list}"
Return exactly two things:
1. The stakeholder group label.
2. A brief justification for if doesnt fit in any category.
"""

        try:
            response = model.generate_content(prompt)
            lines = response.text.strip().split('\n')

            # Parse the response
            stakeholder = ""
            justification = ""
            # for line in lines:
            #     if line.startswith("1"):
            #         stakeholder = line.replace("1", "").strip(": ").strip()
            #     elif line.startswith("2"):
            #         justification = line.replace("2", "").strip(": ").strip()
            if not stakeholder:
                stakeholder = lines[0].strip()
            if not justification and len(lines) > 1:
                justification = lines[1].strip()
            elif not justification:
                justification = "No justification provided."

            stakeholder_list.append(stakeholder)
            justification_list.append(justification)

            print(f"Row {idx+1}: {stakeholder}")
            time.sleep(1)  # Avoid rate limits
        except Exception as e:
            print(f" Error processing row {idx+1}: {e}")
            stakeholder_list.append("Error")
            justification_list.append("Error in classification.")

    # Add the new columns
    df['Stakeholder Group'] = stakeholder_list
    df['Justification'] = justification_list
    os.makedirs(os.path.dirname(output_excel), exist_ok=True)
    # Save the updated Excel
    df.to_excel(output_excel, index=False)
    print(f"\n Classification completed and saved to: {output_excel}")

# --- Example Usage ---
if __name__ == "__main__":
    api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"  # Replace with your real API key
    input_excel = "D:/Prompt_validation/Analyse_actions/Clustered_Energy_Actions_with_Targets.xlsx"
    output_excel = "D:/Prompt_validation/Analyse_actions/Clustered_Energy_Actions_with_Stakeholders.xlsx"

    classify_actions_with_gemini(api_key, input_excel, output_excel)
