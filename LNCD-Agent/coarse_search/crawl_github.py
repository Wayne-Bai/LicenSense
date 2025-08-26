import requests
import json
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from utils.path_utils import here

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

def check_rate_limit(headers: Dict[str, str]) -> bool:
    remaining = int(headers.get("X-RateLimit-Remaining", 1))
    reset_time = int(headers.get("X-RateLimit-Reset", time.time() + 60))
    if remaining == 0:
        wait_seconds = reset_time - time.time()
        wait_seconds = max(wait_seconds, 0)
        print(f"Rate limit exceeded. Sleeping for {wait_seconds:.2f} seconds...")
        time.sleep(wait_seconds + 5)
        return True
    return False

def search_repositories_with_date_range(
    keyword: str,
    github_token: str,
    start_date: str,
    end_date: str,
    per_page: int = 100,
    max_pages: int = 10
) -> List[Dict[str, Any]]:
    headers = {'Authorization': f'token {github_token}'}
    all_repos = []

    for page in range(1, max_pages + 1):
        params = {
            'q': f"{keyword} created:{start_date}..{end_date}",
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }

        while True:
            response = requests.get(GITHUB_SEARCH_URL, headers=headers, params=params)
            if response.status_code == 403 and "rate limit" in response.text.lower():
                if check_rate_limit(response.headers):
                    continue  # Retry after waiting
            elif response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                return all_repos

            break  # Break retry loop if success or non-retryable error

        items = response.json().get('items', [])
        if not items:
            break
        all_repos.extend(items)
        print(f"Fetched {len(items)} repos on page {page} ({start_date} to {end_date})")

    return all_repos

def partition_and_search(
    keyword: str,
    github_token: str,
    start_date: datetime,
    end_date: datetime,
    interval_days: int = 30
) -> List[Dict[str, Any]]:
    all_results = []
    current = start_date

    while current < end_date:
        next_date = min(current + timedelta(days=interval_days), end_date)
        print(f"Searching from {current.date()} to {next_date.date()}")
        repos = search_repositories_with_date_range(
            keyword,
            github_token,
            current.strftime("%Y-%m-%d"),
            next_date.strftime("%Y-%m-%d")
        )
        all_results.extend(repos)
        current = next_date

    print(f"Total repositories fetched: {len(all_results)}")
    return all_results

def save_repositories_to_file(repositories: List[Dict[str, Any]], filename: str) -> None:
    with open(here(filename), 'w', encoding='utf-8') as f:
        json.dump(repositories, f, indent=2)
    print(f"Saved {len(repositories)} repositories to {filename}")

def search_github(KEYWORD):
    GITHUB_TOKEN = "ghp_xxx" # Replace with your actual token
    OUTPUT_FILE = f"github_repos_{KEYWORD}.json"

    START_DATE = datetime(2025, 1, 1) # Based on the requirement to search
    END_DATE = datetime(2025, 4, 15)

    repos = partition_and_search(KEYWORD, GITHUB_TOKEN, START_DATE, END_DATE)
    save_repositories_to_file(repos, OUTPUT_FILE)

if __name__ == "__main__":
    KEYWORD = "BRSET"  

    GITHUB_TOKEN = "ghp_xxx" # Replace with your actual token
    OUTPUT_FILE = f"github_repos_{KEYWORD}.json"

    START_DATE = datetime(2025, 3, 1) # Based on the requirement to search
    END_DATE = datetime(2025, 4, 15)

    repos = partition_and_search(KEYWORD, GITHUB_TOKEN, START_DATE, END_DATE)
    save_repositories_to_file(repos, OUTPUT_FILE)