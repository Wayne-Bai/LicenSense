import json
from openai import OpenAI
import re
from typing import Dict, Any, List
from utils.path_utils import here

def extract_json_from_text(text: str) -> Dict[str, Any]:
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

def check_downstream_usage_kaggle(dataset_info: Dict[str, Any],
                                  original_dataset_info: Dict[str, Any],
                                  openai_api_key: str) -> Dict[str, Any]:
    api_key = openai_api_key
    client = OpenAI(api_key=api_key)

    MAX_DATASET_CARD_LENGTH = 8000

    dataset_card = dataset_info.get('dataset_card', '')
    if dataset_card and len(dataset_card) > MAX_DATASET_CARD_LENGTH:
        dataset_card = dataset_card[:MAX_DATASET_CARD_LENGTH] + "\n... [truncated]"

    prompt = f"""You are an expert in analyzing dataset usage.
Given the following Kaggle dataset information:
-------------------------------------------
Dataset Ref: {dataset_info.get('ref')}
Title: {dataset_info.get('title')}
Subtitle: {dataset_info.get('subtitle')}
License: {dataset_info.get('licenseName')}
Dataset Card:
{dataset_card}

And the original dataset information:
-------------------------------------------
Dataset Title: {original_dataset_info.get('title')}
Dataset Topics: {', '.join(original_dataset_info.get('topics', []))}
Dataset Name: {original_dataset_info.get('name')}
Representative Words: {', '.join(original_dataset_info.get('representative_words', []))}
Website: {original_dataset_info.get('website')}

Determine whether this Kaggle dataset is a true downstream usage of the original dataset.
Downstream usage means that the dataset uses, evaluates, or extends the original dataset.
Return your answer in valid JSON format with the following keys:
- "is_downstream": a boolean value (true or false)
- "reason": a brief explanation of your decision.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Adjust to the desired model
            messages=[
                {"role": "system", "content": "You are an expert on dataset usage analysis."},
                {"role": "user", "content": prompt}
            ],
        )
        output_text = response.choices[0].message.content.strip()
        return extract_json_from_text(output_text)
    except Exception as e:
        return {"is_downstream": False, "reason": f"Error calling OpenAI API: {e}"}

def process_kaggle_datasets_file(input_filename: str, output_filename: str,
                                 openai_api_key: str, original_dataset_info: Dict[str, Any]) -> None:
    try:
        with open(here(input_filename), 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"Error loading {input_filename}: {e}")
        return

    processed_datasets = []
    for index, ds in enumerate(datasets, 1):
        print(f"Processing dataset {index}/{len(datasets)}: {ds.get('ref')}")
        downstream_result = check_downstream_usage_kaggle(ds, original_dataset_info, openai_api_key)
        new_entry = {
            "ref": ds.get("ref"),
            "title": ds.get("title"),
            "license": ds.get("licenseName"),
            "downstream_usage": downstream_result
        }
        processed_datasets.append(new_entry)

    try:
        with open(here(output_filename), 'w', encoding='utf-8') as f:
            json.dump(processed_datasets, f, indent=4)
        print(f"Processed {len(processed_datasets)} datasets. Saved results to {output_filename}")
    except Exception as e:
        print(f"Error saving to {output_filename}: {e}")

def filter_kaggle(input_filename: str, output_filename: str,
                  openai_api_key: str, original_dataset_info: Dict[str, Any]) -> None:
    """
    Filters Kaggle datasets based on downstream usage analysis.
    
    Args:
        input_filename (str): Path to the input JSON file containing Kaggle datasets.
        output_filename (str): Path to the output JSON file for filtered datasets.
        openai_api_key (str): Your OpenAI API key.
        original_dataset_info (Dict[str, Any]): Original dataset information for comparison.
    """
    process_kaggle_datasets_file(input_filename, output_filename, openai_api_key, original_dataset_info)

if __name__ == "__main__":
    OPENAI_API_KEY = "sk-xxx" # Replace with your actual token
    KEYWORD = "BRSET"
    INPUT_FILE = f"processed_kaggle_{KEYWORD}.json"
    OUTPUT_FILE = f"final_processed_kaggle_{KEYWORD}.json"

    dataset_info = {
        "title": "A Brazilian Multilabel Ophthalmological Dataset (BRSET)",
        "topics": ["MegaFace is a large-scale dataset and benchmark used for evaluating face recognition algorithms. It consists of over 1 million faces and is designed to test how well algorithms can handle a large number of distractors ", "BRSET"],
        "name": "BRSET",
        "representative_words": ["BRSET"],
        "website": "https://physionet.org/content/brazilian-ophthalmological/1.0.1/"
    }



    # dataset_info = {
    #     "title": "Large-scale CelebFaces Attributes (CelebA) Dataset",
    #     "topics": ["face recognition", "CelebA"],
    #     "name": "CelebA",
    #     "representative_words": ["CelebA"],
    #     "website": "https://mmlab.ie.cuhk.edu.hk/projects/CelebA.html"
    # }

    process_kaggle_datasets_file(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)