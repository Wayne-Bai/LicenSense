import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.path_utils import here

GITHUB_API_BASE = "https://api.github.com"

def fetch_repo_readme(repo_full_name: str, github_token: str) -> Optional[str]:
    """
    Fetch the README content of a GitHub repository with timeout, rate limit handling,
    and infinite retry on errors.
    """
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    readme_url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/readme"

    while True:
        try:
            response = requests.get(readme_url, headers=headers, timeout=10)

            # Rate limit handling
            remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
            reset = int(response.headers.get("X-RateLimit-Reset", time.time()))

            if remaining == 0 or response.status_code in [403, 429]:
                wait_time = reset - time.time()
                wait_time = max(wait_time, 0)
                print(f"[INFO] Rate limit hit or throttled. Sleeping for {int(wait_time)+5} seconds...")
                time.sleep(wait_time + 5)
                continue

            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            else:
                print(f"[ERROR] Failed to fetch README for {repo_full_name} (status {response.status_code})")
                return None

        except requests.exceptions.ConnectTimeout:
            print(f"[TIMEOUT] Connection timeout for {repo_full_name}. Retrying in 10 seconds...")
            time.sleep(10)
        except requests.RequestException as e:
            print(f"[EXCEPTION] Network error for {repo_full_name}: {e}. Retrying in 10 seconds...")
            time.sleep(10)

def process_repository(repo: Dict[str, Any], github_token: str) -> Dict[str, Any]:
    """
    Process a single GitHub repository to extract metadata and README.
    """
    processed = {
        "name": repo.get("name"),
        "full_name": repo.get("full_name"),
        "license": repo.get("license", {}).get("name") if repo.get("license") else None,
        "topics": repo.get("topics", []),
    }

    readme_content = fetch_repo_readme(repo.get("full_name", ""), github_token)
    processed["readme"] = readme_content if readme_content else None

    return processed

def process_repositories(repos: List[Dict[str, Any]], github_token: str) -> List[Dict[str, Any]]:
    """
    Process a list of repositories and collect results.
    """
    processed_all = []
    total = len(repos)

    for i, repo in enumerate(repos, 1):
        processed = process_repository(repo, github_token)
        processed_all.append(processed)

        if i % 10 == 0 or i == total:
            print(f"[PROGRESS] Processed {i}/{total} repositories")

    return processed_all

def save_processed_repositories(processed_repos: List[Dict[str, Any]], filename: str) -> None:
    """
    Save processed repository data to a JSON file.
    """
    with open(here(filename), 'w', encoding='utf-8') as f:
        json.dump(processed_repos, f, indent=4)
    print(f"✅ Saved {len(processed_repos)} processed repositories to {filename}")

def clean_github_data(KEYWORD):
    GITHUB_TOKEN = "ghp_xxx"  # Replace with your GitHub token
    input_file = f"github_repos_{KEYWORD}.json"
    output_file = f"processed_github_repos_{KEYWORD}.json"

    try:
        with open(here(input_file), 'r', encoding='utf-8') as f:
            repos_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {input_file}: {e}")
        repos_data = []

    if repos_data:
        print(f"[INFO] Loaded {len(repos_data)} repositories.")
        processed_data = process_repositories(repos_data, GITHUB_TOKEN)
        save_processed_repositories(processed_data, output_file)
    else:
        print("⚠️ No repository data to process.")

if __name__ == "__main__":
    GITHUB_TOKEN = "ghp_xxx"  # Replace with your GitHub token
    KEYWORD = "BRSET"
    input_file = f"github_repos_{KEYWORD}.json"
    output_file = f"processed_github_repos_{KEYWORD}.json"

    try:
        with open(here(input_file), 'r', encoding='utf-8') as f:
            repos_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {input_file}: {e}")
        repos_data = []

    if repos_data:
        print(f"[INFO] Loaded {len(repos_data)} repositories.")
        processed_data = process_repositories(repos_data, GITHUB_TOKEN)
        save_processed_repositories(processed_data, output_file)
    else:
        print("⚠️ No repository data to process.")
