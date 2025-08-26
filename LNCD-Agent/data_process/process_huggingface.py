import requests
import json
import time
from typing import List, Dict, Any, Optional
from utils.path_utils import here

HF_TOKEN = None  # Optional: Replace with your Hugging Face token (e.g., "hf_xxx")
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

HF_CARD_URL = "https://huggingface.co/datasets/{dataset_id}/raw/main/README.md"
HF_TREE_BASE_URL = "https://huggingface.co/api/datasets/{dataset_id}/tree/main"

def safe_request(url: str, headers: Optional[Dict[str, str]] = None, backoff_factor: int = 2):
    """
    Make a GET request that retries forever on rate-limit or server errors.
    """
    attempt = 0
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                wait_time = retry_after * backoff_factor
                print(f"[WARN] 429 Rate limit hit for {url}. Sleeping {wait_time}s...")
                time.sleep(wait_time)
            elif response.status_code in [500, 503]:
                wait_time = backoff_factor ** attempt
                print(f"[WARN] Server error {response.status_code} on {url}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                attempt += 1
            else:
                print(f"[ERROR] Failed request to {url}. Status: {response.status_code}")
                return None
        except requests.exceptions.ConnectTimeout:
            print(f"[TIMEOUT] Connection timeout for {url}. Retrying in 10 seconds...")
            time.sleep(10)
        except requests.RequestException as e:
            print(f"[EXCEPTION] Network error for {url}: {e}. Retrying in 10 seconds...")
            time.sleep(10)

def extract_license(tags: List[str]) -> Optional[str]:
    for tag in tags:
        if tag.startswith("license:"):
            return tag.replace("license:", "")
    return None

def fetch_dataset_card(dataset_id: str) -> Optional[str]:
    url = HF_CARD_URL.format(dataset_id=dataset_id)
    response = safe_request(url, headers=HF_HEADERS)
    if response:
        return response.text
    print(f"[INFO] No README found for {dataset_id}")
    return None

def fetch_recursive_file_paths(dataset_id: str, path: str = "") -> List[str]:
    url = HF_TREE_BASE_URL.format(dataset_id=dataset_id)
    if path:
        url += f"/{path}"

    response = safe_request(url, headers=HF_HEADERS)
    if not response:
        print(f"[WARN] Failed to fetch files for {dataset_id} at path '{path}'")
        return []

    items = response.json()
    all_files = []
    for item in items:
        if item['type'] == 'file':
            all_files.append(item['path'])
        elif item['type'] == 'directory':
            sub_path = item['path']
            all_files.extend(fetch_recursive_file_paths(dataset_id, sub_path))
    return all_files

def process_datasets(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    total = len(data)
    for idx, entry in enumerate(data, 1):
        dataset_id = entry.get("id")
        tags = entry.get("tags", [])

        license_name = extract_license(tags)
        readme = fetch_dataset_card(dataset_id)
        all_files = fetch_recursive_file_paths(dataset_id)

        result.append({
            "id": dataset_id,
            "license": license_name,
            "dataset_card": readme,
            "files": all_files
        })

        print(f"[PROGRESS] Processed {idx}/{total}: {dataset_id}")

    return result

def save_to_json(data: List[Dict[str, Any]], filename: str) -> None:
    with open(here(filename), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved {len(data)} entries to {filename}")

def clean_huggingface_data(KEYWORD):
    INPUT_FILE = f"huggingface_datasets_{KEYWORD}.json"
    OUTPUT_FILE = f"processed_huggingface_{KEYWORD}.json"

    try:
        with open(here(INPUT_FILE), 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load input file: {e}")
        datasets = []

    if datasets:
        print(f"[INFO] Loaded {len(datasets)} datasets to process.")
        processed = process_datasets(datasets)
        save_to_json(processed, OUTPUT_FILE)
    else:
        print("⚠️ No datasets to process.")

if __name__ == "__main__":
    KEYWORD = "BRSET" 
    INPUT_FILE = f"huggingface_datasets_{KEYWORD}.json"
    OUTPUT_FILE = f"processed_huggingface_{KEYWORD}.json"

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load input file: {e}")
        datasets = []

    if datasets:
        print(f"[INFO] Loaded {len(datasets)} datasets to process.")
        processed = process_datasets(datasets)
        save_to_json(processed, OUTPUT_FILE)
    else:
        print("⚠️ No datasets to process.")
