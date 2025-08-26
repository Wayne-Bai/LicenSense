import requests
from io import BytesIO
from PyPDF2 import PdfReader
import pandas as pd
from utils.path_utils import here

def extract_intro_from_pdf(pdf_url):
    # Download the PDF from the URL
    response = requests.get(pdf_url)
    response.raise_for_status()  # Good for checking the response status

    # Load the PDF into a PyPDF2 reader
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)

    # Combine all the text from the PDF
    full_text = ""
    for page in reader.pages:
        if page.extract_text():
            full_text += page.extract_text() or ""  # Ensure non-None concatenation

    intro_end = full_text.lower().find("references\n")  # Assumed keyword for end of intro

    if intro_end == -1:
        raise ValueError("Seperatrion by References could not done.")

    introduction_text = full_text[:intro_end]
    return introduction_text.strip()

def check_open_source_intro(content):
    open_pattern = ['physionet', 'github', 'huggingface', 'kaggle', 'zenodo', 'tfhub', 'monai']
    open_string = ''
    for i in open_pattern:
        if i in content:
            open_string += i + ', '
    
    return open_string.rstrip(', ') if open_string else 'N/A'  # Remove trailing comma

def load_csv(file_path):
    return pd.read_csv(here(file_path))

def check_open_source(KEYWORD):
    cited_by_paper = load_csv(f'cited_papers_{KEYWORD}.csv')
    output_file = f'Open_Source_Check_with_{KEYWORD}.csv'
    osc_save = pd.DataFrame()  # Initialize DataFrame to save results

    for i in range(cited_by_paper.shape[0]):
        if cited_by_paper.iloc[i]['Source Type'] == 'PDF':  # Correct indexing of iloc
            pdf_url = cited_by_paper.iloc[i]['Source Link']  # Correct indexing of iloc
            print(pdf_url)

            try:
                intro_content = extract_intro_from_pdf(pdf_url)
                open_source = check_open_source_intro(intro_content)
                cited_by_paper.at[i, 'Open Source Platform'] = open_source  # Correct assignment
                osc_save = pd.concat([osc_save, pd.DataFrame([cited_by_paper.iloc[i]])], ignore_index=True)
            except Exception as e:
                print(f"Error processing {pdf_url}: {str(e)}")

    osc_save.to_csv(here(output_file), index=False)

if __name__ == "__main__":

    KEYWORD = "BRSET"  # Example keyword

    cited_by_paper = load_csv(f'cited_papers_{KEYWORD}.csv')
    output_file = f'Open_Source_Check_with_{KEYWORD}.csv'
    osc_save = pd.DataFrame()  # Initialize DataFrame to save results

    for i in range(cited_by_paper.shape[0]):
        if cited_by_paper.iloc[i]['Source Type'] == 'PDF':  # Correct indexing of iloc
            pdf_url = cited_by_paper.iloc[i]['Source Link']  # Correct indexing of iloc
            print(pdf_url)

            try:
                intro_content = extract_intro_from_pdf(pdf_url)
                open_source = check_open_source_intro(intro_content)
                cited_by_paper.at[i, 'Open Source Platform'] = open_source  # Correct assignment
                osc_save = pd.concat([osc_save, pd.DataFrame([cited_by_paper.iloc[i]])], ignore_index=True)
            except Exception as e:
                print(f"Error processing {pdf_url}: {str(e)}")

    osc_save.to_csv(output_file, index=False)
