import requests
import json
import time
from typing import List, Dict, Any
from requests.auth import HTTPBasicAuth
from utils.path_utils import here

KAGGLE_DATASETS_URL = "https://www.kaggle.com/api/v1/datasets/list"

def search_datasets_by_keyword(
    keyword: str,
    kaggle_username: str,
    kaggle_key: str,
    per_page: int = 100,
    max_pages: int = None
) -> List[Dict[str, Any]]:
    auth = HTTPBasicAuth(kaggle_username, kaggle_key)
    all_datasets = []
    page = 1
    total_fetched = 0

    while True:
        if max_pages and page > max_pages:
            break

        params = {
            "search": keyword,
            "page": page,
            "pageSize": per_page
        }

        attempt = 0
        while True:
            try:
                response = requests.get(KAGGLE_DATASETS_URL, params=params, auth=auth, timeout=10)

                if response.status_code == 200:
                    items = response.json()
                    if not items:
                        print(f"[DONE] No more datasets at page {page}.")
                        return all_datasets
                    all_datasets.extend(items)
                    total_fetched += len(items)
                    print(f"[INFO] Fetched {len(items)} datasets from page {page}. Total: {total_fetched}")
                    page += 1
                    break  # success

                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    wait_time = max(retry_after * (2 ** attempt), 5)
                    print(f"[WARN] 429 Rate limit hit. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    attempt += 1

                elif response.status_code == 503:
                    wait_time = 5 * (2 ** attempt)
                    print(f"[WARN] 503 Service Unavailable. Sleeping {wait_time}s...")
                    time.sleep(wait_time)
                    attempt += 1

                else:
                    print(f"[ERROR] Status {response.status_code}: {response.text}")
                    return all_datasets

            except requests.exceptions.RequestException as e:
                print(f"[EXCEPTION] Request error: {e}. Sleeping 10s before retry...")
                time.sleep(10)
                attempt += 1

    return all_datasets

def save_datasets_to_file(datasets: List[Dict[str, Any]], filename: str) -> None:
    with open(here(filename), 'w', encoding='utf-8') as f:
        json.dump(datasets, f, indent=4)
    print(f"💾 Saved {len(datasets)} datasets to {filename}")

def search_kaggle(KEYWORD: str):
    KAGGLE_USERNAME = "xxx"
    KAGGLE_KEY = "xxx" # Replace with your actual token
    OUTPUT_FILE = f"kaggle_datasets_{KEYWORD}.json"
    print(f"[START] Crawling Kaggle datasets for keyword: '{KEYWORD}'")
    start_time = time.time()

    datasets = search_datasets_by_keyword(KEYWORD, KAGGLE_USERNAME, KAGGLE_KEY)
    save_datasets_to_file(datasets, OUTPUT_FILE)

    duration = time.time() - start_time
    print(f"[DONE] Total datasets fetched: {len(datasets)} in {duration:.2f}s")

if __name__ == "__main__":
    KEYWORD = "BRSET"
    KAGGLE_USERNAME = "xxx"
    KAGGLE_KEY = "xxx" # Replace with your actual token
    OUTPUT_FILE = f"kaggle_datasets_{KEYWORD}.json"

    print(f"[START] Crawling Kaggle datasets for keyword: '{KEYWORD}'")
    start_time = time.time()

    datasets = search_datasets_by_keyword(KEYWORD, KAGGLE_USERNAME, KAGGLE_KEY)
    save_datasets_to_file(datasets, OUTPUT_FILE)

    duration = time.time() - start_time
    print(f"[DONE] Total datasets fetched: {len(datasets)} in {duration:.2f}s")

