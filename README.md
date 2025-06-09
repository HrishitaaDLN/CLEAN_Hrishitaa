# PDF Action Extractor

This script analyzes PDF reports using Google's Gemini AI to extract actions related to stationary energy, waste, and transport. It then generates an Excel spreadsheet with the findings and statistical analysis.

## Features

- Uses Gemini AI for intelligent action extraction and categorization
- Processes multiple PDF files
- Categorizes actions into:
  - Stationary Energy
  - Waste
  - Transport
  - Other
- Generates an Excel spreadsheet with two sheets:
  - Actions: Lists all extracted actions with their categories and source files
  - Statistics: Shows the percentage distribution of actions across categories

## Prerequisites

1. A Google Cloud account with Vertex AI API enabled
2. Google Cloud credentials set up on your machine
3. Python 3.7 or higher

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=us-central1  # or your preferred region
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   ```

   You can either:
   - Set these directly in your environment
   - Create a `.env` file with these variables
   - Export them in your shell session

## Usage

1. Place all your PDF reports in a single directory
2. Run the script:
   ```
   python extract_actions.py
   ```
3. When prompted, enter the path to the directory containing your PDF files
4. The script will process each PDF file using Gemini AI and generate an `action_analysis.xlsx` file

## Output

The script generates an Excel file (`action_analysis.xlsx`) with two sheets:

1. **Actions**
   - Action: The extracted action text
   - Category: The categorization (Stationary Energy, Waste, Transport, or Other)
   - Source File: The PDF file where the action was found

2. **Statistics**
   - Total number of actions found
   - Percentage of actions in each category

## Notes

- The script uses Gemini AI to intelligently identify and categorize actions
- Large PDF files are automatically split into smaller chunks for processing
- Make sure your Google Cloud credentials are properly set up and have the necessary permissions
- The script requires an active internet connection to use the Gemini AI service 