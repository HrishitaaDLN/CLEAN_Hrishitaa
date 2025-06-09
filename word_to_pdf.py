from pathlib import Path
from docx2pdf import convert
import os

def convert_word_to_pdf(source_folder: str, output_folder: str = None) -> None:
    """
    Converts all Word (.docx) files in the specified source folder to PDF files.

    Args:
        source_folder (str): Path to the folder containing Word files.
        output_folder (str, optional): Path to the folder to save converted PDFs. If None, saves PDFs in the same folder.
    """
    source_path = Path(source_folder)
    if not source_path.is_dir():
        print(f"Error: The specified folder '{source_folder}' does not exist.")
        return

    # Create output folder if specified
    if output_folder:
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = source_path

    docx_files = list(source_path.glob("*.docx"))
    if not docx_files:
        print("No Word (.docx) files found in the specified folder.")
        return

    for docx_file in docx_files:
        try:
            output_file = output_path / f"{docx_file.stem}.pdf"
            print(f"Converting '{docx_file.name}' to PDF...")
            convert(str(docx_file), str(output_file))
            print(f"Saved PDF: '{output_file.name}'")
        except Exception as e:
            print(f"Error converting '{docx_file.name}': {e}")

    print("\n✅ Conversion process completed.")

# Example usage:
if __name__ == "__main__":
    source_folder_path = r"D:/All Municipality Reports_selected_50_analysis/analysis_output"
    output_folder_path = r"D:/All Municipality Reports_selected_50_analysis/analysis_output/pdfs"  # Optional: specify output folder, or set to None

    convert_word_to_pdf(source_folder=source_folder_path, output_folder=output_folder_path)
