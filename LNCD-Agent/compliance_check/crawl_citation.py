import logging
from serpapi import GoogleSearch
import pandas as pd
from rapidfuzz import fuzz 
from utils.path_utils import here

# Setup logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()])

def get_most_similar_result(results, paper_title):
    """
    Find the most similar result to the given paper title using fuzzy matching,
    aiming for an exact match.
    """
    best_match = None
    highest_score = 0  # Initialize to zero to search for the highest score

    for result in results:
        title = result.get("title", "")
        similarity_score = fuzz.ratio(paper_title.lower(), title.lower())  # Using 'ratio' for exact matching
        if similarity_score > highest_score:  # Find the highest score
            highest_score = similarity_score
            best_match = result
            if highest_score == 100:  # Break if exact match is found
                break

    if best_match:
        logging.info(f"Best match: {best_match.get('title', 'N/A')} with score: {highest_score}")
    else:
        logging.info("No exact match found.")
    return best_match if highest_score == 100 else None

def get_paper_result_id(paper_title, api_key):
    """
    Fetch the 'Cited by' URL for a given paper title using SerpAPI.
    """
    search = GoogleSearch({
        "q": paper_title,
        "engine": "google_scholar",
        "api_key": api_key
    })
    results = search.get_dict()

    if "organic_results" in results:
        most_similar_result = get_most_similar_result(results["organic_results"], paper_title)
        if most_similar_result:
            title = most_similar_result.get('title', 'N/A')
            result_id = most_similar_result.get("result_id", None)
            cited_count = most_similar_result.get('inline_links', {}).get('cited_by', {}).get('total', 0)
            return title, result_id, cited_count

    logging.error(f"No results found for: {paper_title}")
    return None, None, 0

def get_cited_by_papers(result_id, api_key, start_index, cited_count=20):
    """
    Fetch papers that cited the original paper using the result ID.
    """
    params = {
        "api_key": api_key,
        "engine": "google_scholar",
        "hl": "en",
        "cites": result_id,
        "start": start_index,
        "num": cited_count
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def load_csv(file_name):
    """
    Load CSV into DataFrame.
    """
    return pd.read_csv(here(file_name))

def crawl_citation(KEYWORD, TITLE):
    API_KEY = "xxx"  # Replace with your actual SerpAPI key
    # KEYWORD = "BRSET"  # Example keyword
    # TITLE = "A Brazilian multilabel ophthalmological dataset (BRSET)"

    output_csv = f"cited_papers_{KEYWORD}.csv"
    save_cited_paper = pd.DataFrame(columns=['Original', 'Cited By', 'Source Existed', 'Source Type', 'Source Link'])

    logging.info(f"Processing: {TITLE}")

    result_title, result_id, cited_count = get_paper_result_id(TITLE, API_KEY)

    if result_id and cited_count > 0:
        for start_index in range(0, cited_count, 20):
            cited_by_content = get_cited_by_papers(result_id, API_KEY, start_index, 20)
            cited_by_papers = cited_by_content.get('organic_results', [])

            logging.info(f"Found {len(cited_by_papers)} citing papers for: {result_title}")

            for paper in cited_by_papers:
                temp_data = pd.DataFrame([{
                    "Original": TITLE,
                    "Cited By": paper['title'],
                    "Source Existed": "Yes" if "resources" in paper else "No",
                    "Source Type": paper["resources"][0]["file_format"] if "resources" in paper else "N/A",
                    "Source Link": paper["resources"][0]["link"] if "resources" in paper else "N/A"
                }])
                save_cited_paper = pd.concat([save_cited_paper, temp_data], ignore_index=True)

    else:
        logging.error(f"No matching results found for: {TITLE}")

    save_cited_paper.to_csv(output_csv, index=False)
    logging.info(f"Results saved to {output_csv}")


if __name__ == "__main__":
    
    API_KEY = "2417bed1b1d859cef91c0e74ea3cfd826a33ff416696ca6b94f60645d9edc580"  # Replace with your actual SerpAPI key
    KEYWORD = "BRSET"  # Example keyword
    TITLE = "A Brazilian multilabel ophthalmological dataset (BRSET)"

    output_csv = f"cited_papers_{KEYWORD}.csv"
    save_cited_paper = pd.DataFrame(columns=['Original', 'Cited By', 'Source Existed', 'Source Type', 'Source Link'])

    logging.info(f"Processing: {TITLE}")

    result_title, result_id, cited_count = get_paper_result_id(TITLE, API_KEY)

    if result_id and cited_count > 0:
        for start_index in range(0, cited_count, 20):
            cited_by_content = get_cited_by_papers(result_id, API_KEY, start_index, 20)
            cited_by_papers = cited_by_content.get('organic_results', [])

            logging.info(f"Found {len(cited_by_papers)} citing papers for: {result_title}")

            for paper in cited_by_papers:
                temp_data = pd.DataFrame([{
                    "Original": TITLE,
                    "Cited By": paper['title'],
                    "Source Existed": "Yes" if "resources" in paper else "No",
                    "Source Type": paper["resources"][0]["file_format"] if "resources" in paper else "N/A",
                    "Source Link": paper["resources"][0]["link"] if "resources" in paper else "N/A"
                }])
                save_cited_paper = pd.concat([save_cited_paper, temp_data], ignore_index=True)

    else:
        logging.error(f"No matching results found for: {TITLE}")

    save_cited_paper.to_csv(output_csv, index=False)
    logging.info(f"Results saved to {output_csv}")
    # exit()
