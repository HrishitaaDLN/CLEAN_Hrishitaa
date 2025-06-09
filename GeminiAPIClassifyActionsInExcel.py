import google.generativeai as genai
import pandas as pd
import time

# Configure Gemini API
def classify_actions_with_gemini(api_key, input_excel, output_excel):
    try:
        genai.configure(api_key=api_key)
        print("Gemini API configured.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    # Load the Excel file
    df = pd.read_excel(input_excel)
    if 'Action' not in df.columns:
        print("No 'Action' column found in Excel.")
        return

    # Prepare prompt for each action
    model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")

    category_list = []
    justification_list = []
    print("Classifying actions...")

    for idx, action in enumerate(df['Action']):
        if pd.isna(action):
            category_list.append("Other")
            justification_list.append("No action provided.")
            continue

        prompt = f"""
Objective:
Classify the following energy mitigation action into the correct category based on the C40 Cities and Global Protocol for Community-Scale Greenhouse Gas Emission Inventories (GPC) framework.

The classification depends on:

The type of emissions the action mitigates (e.g., fuel combustion, electricity consumption, transmission losses, or fugitive emissions)

The sector or activity targeted by the action (e.g., residential buildings, commercial facilities, industrial processes, energy generation, agriculture, or fugitive emissions from fuel systems)

 Categories for Classification:
Classify the action into one of these categories only if the mitigation action aims to reduce emissions from the following sources or activities:

I.1 Residential Buildings
For mitigation actions that aim to reduce:

Emissions from fuel combustion within the city boundary 

Emissions from grid-supplied energy consumed within the city boundary

Emissions from transmission and distribution losses of grid-supplied energy

I.2 Commercial and Institutional Buildings and Facilities
For mitigation actions that aim to reduce:

Emissions from fuel combustion within the city boundary 

Emissions from grid-supplied energy consumed within the city boundary 

Emissions from transmission and distribution losses of grid-supplied energy

I.3 Manufacturing Industries and Construction
For mitigation actions that aim to reduce:

Emissions from fuel combustion within the city boundary 

Emissions from grid-supplied energy consumed within the city boundary 

Emissions from transmission and distribution losses of grid-supplied energy

I.4 Energy Industries
For mitigation actions that aim to reduce:

Emissions from energy used in power plant auxiliary operations within the city boundary

Emissions from grid-supplied energy used in power plant auxiliary operations

Emissions from transmission and distribution losses of grid-supplied energy used in power plant auxiliary operations

Emissions from energy generation supplied to the grid

I.5 Agriculture, Forestry, and Fishing Activities
For mitigation actions that aim to reduce:

Emissions from fuel combustion within the city boundary 

Emissions from grid-supplied energy consumed within the city boundary 

Emissions from transmission and distribution losses of grid-supplied energy

I.6 Non-Specified Sources
For mitigation actions that aim to reduce:

Emissions from fuel combustion within the city boundary 

Emissions from grid-supplied energy consumed within the city boundary 

Emissions from transmission and distribution losses of grid-supplied energy

I.7 Fugitive Emissions from Mining, Processing, Storage, and Transportation of Coal
For mitigation actions that aim to reduce:

Emissions from fugitive emissions from coal systems within the city boundary

I.8 Fugitive Emissions from Oil and Natural Gas Systems
For mitigation actions that aim to reduce:

Emissions from fugitive emissions from oil and natural gas systems within the city boundary

Instructions for Classification:
1.Read the mitigation action description carefully.
2.Determine what type of emissions the action targets:

Fuel combustion emissions 
Grid-supplied electricity consumption 
Transmission and distribution losses 
Fugitive emissions from coal, oil, or natural gas systems 

3. Determine the sector or activity associated with the action:

Buildings (residential, commercial, industrial)
Energy generation facilities
Agriculture, forestry, or fishing
Fugitive emissions from fuel systems

4. Classify the action into one of the categories (I.1 to I.8).

5. Provide a clear justification for the classification, explaining:

The type of emissions mitigated
The sector/activity
The reasoning for the chosen category

Action: "{action}"
Only return the category name and justification for it.

"""

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Extract category and justification (assuming first line = category, rest = justification)
            lines = response_text.split('\n')
            category = lines[0].strip()
            justification = " ".join([line.strip() for line in lines[1:]]).strip() if len(lines) > 1 else "No justification provided."

            category_list.append(category)
            justification_list.append(justification)

            print(f"Row {idx+1}: {category} - {justification}")
            time.sleep(1)  # Respectful pause to avoid rate limits
        except Exception as e:
            print(f"Error processing row {idx+1}: {e}")
            category_list.append("Other")
            justification_list.append("Error in classification.")

    # Add the new columns
    df['GHG Protocol Category'] = category_list
    df['Justification'] = justification_list

    # Save the updated Excel
    df.to_excel(output_excel, index=False)
    print(f"\nClassification completed and saved to: {output_excel}")

# --- Example Usage ---
if __name__ == "__main__":
    api_key = "AIzaSyDZ1hkeltOGVCVMT6h_lRZGNpyfIgwDOeY"  # Replace with your actual API key
    input_excel = "D:/Prompt_validation/Analyse_actions/Clustered_Energy_Actions_updates.xlsx"
    output_excel = "D:/Prompt_validation/Analyse_actions/Clustered_Energy_Actions_with_Targets.xlsx"

    classify_actions_with_gemini(api_key, input_excel, output_excel)