import json
from openai import OpenAI
import re
from typing import Dict, Any, List, Optional
from utils.path_utils import here

def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extracts JSON data from a string by searching for a JSON code block delimited by ```json ... ```.
    If not found, attempts to parse the entire text as JSON.
    
    Args:
        text (str): The text that may contain a JSON code block.
    
    Returns:
        Dict[str, Any]: The parsed JSON as a Python dictionary, or an empty dict on failure.
    """
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing JSON from code block: {e}")
            return {}
    else:
        try:
            return json.loads(text)
        except Exception as e:
            print(f"Error parsing JSON from full text: {e}")
            return {}

def check_downstream_usage_hf(dataset_info: Dict[str, Any],
                              original_dataset_info: Dict[str, Any],
                              openai_api_key: str) -> Dict[str, Any]:
    """
    Uses the OpenAI API to determine whether a Hugging Face dataset is a true downstream usage
    of a given original dataset. The decision is based on the dataset's id, dataset card, and file list.
    
    If the dataset card or file list is too long, they are trimmed before constructing the prompt.
    
    Args:
        dataset_info (Dict[str, Any]): Hugging Face dataset data (should include 'id', 'dataset_card', and 'files').
        original_dataset_info (Dict[str, Any]): Original dataset information with keys such as 'title',
                                                'topics', 'name', 'representative_words', and 'website'.
        openai_api_key (str): Your OpenAI API key.
    
    Returns:
        Dict[str, Any]: A dictionary with:
            - "is_downstream": a boolean indicating whether the dataset is downstream usage.
            - "reason": a brief explanation of the decision.
    """
    api_key = openai_api_key
    client = OpenAI(api_key=api_key)

    # Define maximum lengths (in characters) for long fields
    MAX_DATASET_CARD_LENGTH = 5000
    MAX_FILE_LIST_LENGTH = 2000

    # Trim the dataset card if necessary
    hf_dataset_card = dataset_info.get('dataset_card', '')
    if hf_dataset_card and len(hf_dataset_card) > MAX_DATASET_CARD_LENGTH:
        hf_dataset_card = hf_dataset_card[:MAX_DATASET_CARD_LENGTH] + "\n... [truncated]"

    # Join the file list and trim if necessary
    files_list = dataset_info.get('files', [])
    hf_files = ', '.join(files_list)
    if len(hf_files) > MAX_FILE_LIST_LENGTH:
        hf_files = hf_files[:MAX_FILE_LIST_LENGTH] + "\n... [truncated]"

    prompt = f"""You are an expert in analyzing dataset usage.
Given the following Hugging Face dataset information:
-------------------------------------------
Dataset ID: {dataset_info.get('id')}
Dataset Card:
{hf_dataset_card}
File List: {hf_files}

And the original dataset information:
-------------------------------------------
Dataset Title: {original_dataset_info.get('title')}
Dataset Topics: {', '.join(original_dataset_info.get('topics', []))}
Dataset Name: {original_dataset_info.get('name')}
Representative Words: {', '.join(original_dataset_info.get('representative_words', []))}
Website: {original_dataset_info.get('website')}

Determine whether this dataset is a true downstream usage of the original dataset.
Downstream usage means that the dataset uses, evaluates, or extends the original dataset (or its methods/code).
Return your answer in valid JSON format with the following keys:
- "is_downstream": a boolean value (true or false)
- "reason": a brief explanation of your decision.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Adjust the model if needed
            messages=[
                {"role": "system", "content": "You are an expert on dataset usage analysis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8192
        )
        output_text = response.choices[0].message.content.strip()
        result = extract_json_from_text(output_text)
        return result
    except Exception as e:
        return {"is_downstream": False, "reason": f"Error calling OpenAI API: {e}"}

def process_datasets_file(input_filename: str, output_filename: str,
                          openai_api_key: str, original_dataset_info: Dict[str, Any]) -> None:
    """
    Loads Hugging Face dataset data from an input JSON file, uses the OpenAI API to analyze
    downstream usage for each dataset, and saves a new JSON file that includes the 'id',
    'license', 'dataset_card', and 'downstream_usage' fields.
    
    The input data is assumed to have at least the following keys:
        - "id"
        - "license" (if available)
        - "dataset_card"
        - "files"
    
    Args:
        input_filename (str): Path to the JSON file containing Hugging Face dataset data.
        output_filename (str): Path where the new JSON file will be saved.
        openai_api_key (str): Your OpenAI API key.
        original_dataset_info (Dict[str, Any]): Original dataset information for comparison.
    """
    try:
        with open(here(input_filename), 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"Error loading {input_filename}: {e}")
        return

    processed_datasets = []
    for index, ds in enumerate(datasets, 1):
        print(f"Processing dataset {index}/{len(datasets)}: {ds.get('id')}")
        downstream_result = check_downstream_usage_hf(ds, original_dataset_info, openai_api_key)
        new_entry = {
            "id": ds.get("id"),
            "license": ds.get("license"),
            "dataset_card": ds.get("dataset_card"),  # Keep the dataset card
            "downstream_usage": downstream_result
        }
        processed_datasets.append(new_entry)

    try:
        with open(here(output_filename), 'w', encoding='utf-8') as f:
            json.dump(processed_datasets, f, indent=4)
        print(f"Processed {len(processed_datasets)} datasets. Saved results to {output_filename}")
    except Exception as e:
        print(f"Error saving to {output_filename}: {e}")

def filter_huggingface(INPUT_FILE: str, OUTPUT_FILE: str,
                             OPENAI_API_KEY: str, dataset_info: Dict[str, Any]) -> None:
    """
    Fine filter Hugging Face datasets based on downstream usage of a dataset.
    
    Args:
        INPUT_FILE (str): Path to the input JSON file with dataset data.
        OUTPUT_FILE (str): Path to the output JSON file for filtered results.
        OPENAI_API_KEY (str): Your OpenAI API key.
        dataset_info (Dict[str, Any]): The original dataset information for comparison.
    """
    process_datasets_file(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)

if __name__ == "__main__":
    # Replace with your actual OpenAI API key
    OPENAI_API_KEY = "sk-xxx" # Replace with your actual token
    
    KEYWORD = "BRSET"  # Example keyword
    # Input file containing Hugging Face dataset info (with keys: id, license, dataset_card, files)
    INPUT_FILE = f"processed_huggingface_{KEYWORD}.json"
    # Output file will include id, license, dataset_card, and downstream_usage fields
    OUTPUT_FILE = f"final_processed_huggingface_{KEYWORD}.json"

    # Original dataset information for comparison
    dataset_info = {
        "title": "A Brazilian Multilabel Ophthalmological Dataset (BRSET)",
        "topics": ["MegaFace is a large-scale dataset and benchmark used for evaluating face recognition algorithms. It consists of over 1 million faces and is designed to test how well algorithms can handle a large number of distractors ", "BRSET"],
        "name": "BRSET",
        "representative_words": ["BRSET"],
        "website": "https://physionet.org/content/brazilian-ophthalmological/1.0.1/"
    }


    process_datasets_file(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)
