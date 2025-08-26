import json
import requests
import time
import threading
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.path_utils import here

# Global rate limiting settings
RATE_LIMIT_INTERVAL = 3  # seconds between requests
_rate_lock = threading.Lock()
_last_request_time = 0

def rate_limited_get(url: str, auth: HTTPBasicAuth = None, **kwargs) -> requests.Response:
    """
    A wrapper around requests.get() that ensures a minimum delay between calls.
    """
    global _last_request_time
    with _rate_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < RATE_LIMIT_INTERVAL:
            sleep_time = RATE_LIMIT_INTERVAL - elapsed
            print(f"[RATE] Sleeping {sleep_time:.2f}s before next request...")
            time.sleep(sleep_time)
        try:
            response = requests.get(url, auth=auth, timeout=10, **kwargs)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error on {url}: {e}. Retrying in 10s...")
            time.sleep(10)
            return rate_limited_get(url, auth=auth, **kwargs)
        _last_request_time = time.time()
        return response

def robust_request(url: str, auth: HTTPBasicAuth, initial_delay: int = 10) -> Dict:
    """
    Makes a rate-limited GET request and retries indefinitely on 429 (rate limit) and server errors.
    """
    delay = initial_delay
    attempt = 0
    while True:
        response = rate_limited_get(url, auth=auth)
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                print(f"[ERROR] JSON parse error: {e}")
                return {}
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", delay))
            wait_time = retry_after * (2 ** attempt)
            print(f"[RATE LIMIT] 429 Too Many Requests. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            attempt += 1
        elif response.status_code == 503:
            wait_time = delay * (2 ** attempt)
            print(f"[WARN] 503 Service Unavailable. Retrying in {wait_time}s...")
            time.sleep(wait_time)
            attempt += 1
        else:
            print(f"[ERROR] HTTP {response.status_code} for {url}")
            return {}

def get_kaggle_dataset_card(dataset_ref: str, username: str, key: str) -> str:
    """
    Fetches the dataset card (description) for a given Kaggle dataset using HTTPBasicAuth.
    """
    url = f"https://www.kaggle.com/api/v1/datasets/view/{dataset_ref}"
    auth = HTTPBasicAuth(username, key)
    data = robust_request(url, auth)
    return data.get("description", "")

def get_kaggle_dataset_files(dataset_ref: str, username: str, key: str) -> List[str]:
    """
    Fetches the list of file names for a Kaggle dataset using the dataset view endpoint.
    """
    url = f"https://www.kaggle.com/api/v1/datasets/view/{dataset_ref}"
    auth = HTTPBasicAuth(username, key)
    data = robust_request(url, auth)
    files = data.get("datasetFiles", [])
    return [file["name"] for file in files]

def process_kaggle_dataset(dataset: Dict[str, Any], username: str, key: str) -> Dict[str, Any]:
    """
    Processes a single Kaggle dataset entry and enriches it with description and file list.
    """
    dataset_ref = dataset.get("ref", "")
    print(f"[PROCESS] Fetching dataset: {dataset_ref}")

    card = get_kaggle_dataset_card(dataset_ref, username, key)
    time.sleep(1)  # pause between API calls
    files = get_kaggle_dataset_files(dataset_ref, username, key)

    return {
        "ref": dataset_ref,
        "title": dataset.get("titleNullable") or dataset.get("title", ""),
        "subtitle": dataset.get("subtitleNullable") or dataset.get("subtitle", ""),
        "licenseName": dataset.get("licenseNameNullable") or dataset.get("licenseName", ""),
        "dataset_card": card,
        "files": files
    }

def process_kaggle_datasets_file(input_filename: str, output_filename: str,
                                 username: str, key: str, max_workers: int = 2) -> None:
    """
    Loads Kaggle datasets from a JSON file, processes them, and saves the result.
    """
    try:
        with open(here(input_filename), "r", encoding="utf-8") as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {input_filename}: {e}")
        return

    processed_datasets = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_kaggle_dataset, ds, username, key) for ds in datasets]
        for future in as_completed(futures):
            try:
                result = future.result()
                processed_datasets.append(result)
            except Exception as ex:
                print(f"[ERROR] Dataset processing failed: {ex}")

    try:
        with open(here(output_filename), "w", encoding="utf-8") as f:
            json.dump(processed_datasets, f, indent=4)
        print(f"✅ Processed {len(processed_datasets)} datasets and saved to {output_filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save {output_filename}: {e}")

def clean_kaggle_data(KEYWORD):
    INPUT_FILE = f"kaggle_datasets_{KEYWORD}.json"
    OUTPUT_FILE = f"processed_kaggle_{KEYWORD}.json"
    KAGGLE_USERNAME = "waynebai"
    KAGGLE_KEY = "xxx" # Replace with your actual token

    process_kaggle_datasets_file(INPUT_FILE, OUTPUT_FILE, KAGGLE_USERNAME, KAGGLE_KEY)

if __name__ == "__main__":
    KEYWORD = "BRSET" 
    INPUT_FILE = f"kaggle_datasets_{KEYWORD}.json"
    OUTPUT_FILE = f"processed_kaggle_{KEYWORD}.json"
    KAGGLE_USERNAME = "waynebai"
    KAGGLE_KEY = "xxx" # Replace with your actual token

    process_kaggle_datasets_file(INPUT_FILE, OUTPUT_FILE, KAGGLE_USERNAME, KAGGLE_KEY)
