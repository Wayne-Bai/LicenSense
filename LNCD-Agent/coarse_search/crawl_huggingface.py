import requests
import json
import time
from typing import List, Dict, Any, Optional
from utils.path_utils import here

HUGGINGFACE_DATASETS_URL = "https://huggingface.co/api/datasets"

def search_datasets_by_keyword(
    keyword: str,
    hf_token: Optional[str] = None,
    max_retries: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches Hugging Face datasets by keyword using the Hugging Face Hub API,
    with built-in retry logic and rate-limit handling.

    Args:
        keyword (str): The search term.
        hf_token (Optional[str]): Hugging Face API token.
        max_retries (int): Number of retry attempts on 429 errors.

    Returns:
        List[Dict[str, Any]]: List of matching dataset metadata.
    """
    headers = {}
    if hf_token:
        headers['Authorization'] = f"Bearer {hf_token}"

    params = {
        "search": keyword
    }

    for attempt in range(max_retries):
        response = requests.get(HUGGINGFACE_DATASETS_URL, headers=headers, params=params)

        if response.status_code == 200:
            items = response.json()
            print(f"✅ Fetched {len(items)} datasets for keyword: '{keyword}'")
            return items

        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 5))
            wait_time = min(retry_after * (2 ** attempt), 60)
            print(f"[WARN] Rate limit hit (429). Sleeping {wait_time}s... (Attempt {attempt+1}/{max_retries})")
            time.sleep(wait_time)

        else:
            print(f"[ERROR] Failed with status {response.status_code}: {response.text}")
            break

    print(f"[FAIL] Could not fetch datasets for keyword '{keyword}' after {max_retries} attempts.")
    return []

def save_datasets_to_file(datasets: List[Dict[str, Any]], filename: str) -> None:
    """
    Saves the collected dataset data to a JSON file.
    """
    with open(here(filename), 'w', encoding='utf-8') as f:
        json.dump(datasets, f, indent=4)
    print(f"💾 Saved {len(datasets)} datasets to {filename}")

def search_huggingface(KEYWORD):
    HF_TOKEN = "hf_xxx" # Replace with your actual token
    OUTPUT_FILE = f"huggingface_datasets_{KEYWORD}.json"

    datasets = search_datasets_by_keyword(KEYWORD, HF_TOKEN)
    save_datasets_to_file(datasets, OUTPUT_FILE)

if __name__ == "__main__":
    # Example usage
    KEYWORD = "BRSET" 
    HF_TOKEN = "hf_xxx"  # Replace with your actual token
    OUTPUT_FILE = f"huggingface_datasets_{KEYWORD}.json"

    datasets = search_datasets_by_keyword(KEYWORD, HF_TOKEN)
    save_datasets_to_file(datasets, OUTPUT_FILE)
