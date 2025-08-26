import json
from openai import OpenAI
import re
from typing import Dict, Any
from utils.path_utils import here

GITHUB_API_BASE = "https://api.github.com"

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

def check_downstream_usage(repo_info: Dict[str, Any],
                           dataset_info: Dict[str, Any],
                           openai_api_key: str) -> Dict[str, Any]:
    """
    Uses the OpenAI API to determine whether a repository is a downstream usage
    of a given original dataset. The decision is based on the repository's name,
    topics, and README along with the dataset's title, topics, name, and representative words.
    
    Args:
        repo_info (Dict[str, Any]): Repository data with keys 'name', 'topics', and 'readme'.
        dataset_info (Dict[str, Any]): Original dataset information with keys 'title', 'topics',
                                       'name', and 'representative_words'.
        openai_api_key (str): Your OpenAI API key.
    
    Returns:
        Dict[str, Any]: A dictionary with keys:
            - "is_downstream": a boolean indicating whether the repository is downstream usage.
            - "reason": a brief explanation of the decision.
    """
    api_key = openai_api_key
    client = OpenAI(api_key=api_key)

    prompt = f"""You are an expert in analyzing dataset usage.
                Given the following repository information:
                -------------------------------------------
                Repository Name: {repo_info.get('name')}
                Repository Topics: {', '.join(repo_info.get('topics', []))}
                Repository README:
                {repo_info.get('readme')}

                And the original dataset information:
                -------------------------------------------
                Dataset Title: {dataset_info.get('title')}
                Dataset Topics: {', '.join(dataset_info.get('topics', []))}
                Dataset Name: {dataset_info.get('name')}
                Representative Words: {', '.join(dataset_info.get('representative_words', []))}
                Website: {dataset_info.get('website')}

                Determine whether the repository is a downstream usage of the original dataset.
                Downstream usage means that the repository uses, evaluates, or extends the dataset (or its methods/code).
                Return your answer in valid JSON format with the following keys:
                - "is_downstream": a boolean value (true or false)
                - "reason": a brief explanation of your decision.
                """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert on dataset usage analysis."},
                {"role": "user", "content": prompt}
            ],
            # temperature=0.0,
            # max_tokens=200
        )
        output_text = response.choices[0].message.content.strip()
        result = extract_json_from_text(output_text)
        # print(result)
        # exit()
        return result
    except Exception as e:
        return {"is_downstream": False, "reason": f"Error calling OpenAI API: {e}"}

def process_repos_file(input_filename: str, output_filename: str,
                       openai_api_key: str, dataset_info: Dict[str, Any]) -> None:
    """
    Loads repository data from the input JSON file, adds downstream usage analysis
    for each repository using the OpenAI API, and saves the new data to an output JSON file.
    
    Args:
        input_filename (str): Path to the JSON file containing repository data.
        output_filename (str): Path where the new JSON file will be saved.
        openai_api_key (str): Your OpenAI API key.
        dataset_info (Dict[str, Any]): The original dataset information for comparison.
    """
    try:
        with open(here(input_filename), 'r', encoding='utf-8') as f:
            repos_data = json.load(f)
    except Exception as e:
        print(f"Error loading {input_filename}: {e}")
        return

    # Process each repository
    for index, repo in enumerate(repos_data, 1):
        print(f"Processing repo {index}/{len(repos_data)}: {repo.get('full_name')}")
        downstream_result = check_downstream_usage(repo, dataset_info, openai_api_key)
        repo['downstream_usage'] = downstream_result

    # Save the new repository data to the output file
    try:
        with open(here(output_filename), 'w', encoding='utf-8') as f:
            json.dump(repos_data, f, indent=4)
        print(f"Processed {len(repos_data)} repositories. Saved results to {output_filename}")
    except Exception as e:
        print(f"Error saving to {output_filename}: {e}")

def filter_github(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info):
    """
    Fine filter GitHub repositories based on downstream usage of a dataset.
    
    Args:
        INPUT_FILE (str): Path to the input JSON file with repository data.
        OUTPUT_FILE (str): Path to the output JSON file for filtered results.
        OPENAI_API_KEY (str): Your OpenAI API key.
        dataset_info (Dict[str, Any]): The original dataset information for comparison.
    """
    process_repos_file(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)

if __name__ == "__main__":
    # Replace with your actual OpenAI API key
    OPENAI_API_KEY = "sk-xxx" # Replace with your actual token

    # Input file is the JSON file with repo infos from your previous script-
    KEYWORD = "BRSET"
    INPUT_FILE = f"processed_github_repos_{KEYWORD}.json"
    OUTPUT_FILE = f"final_processed_repos_{KEYWORD}.json"

    # Original dataset information for comparison


    dataset_info = {
        "title": "A Brazilian Multilabel Ophthalmological Dataset (BRSET)",
        "topics": ["MegaFace is a large-scale dataset and benchmark used for evaluating face recognition algorithms. It consists of over 1 million faces and is designed to test how well algorithms can handle a large number of distractors ", "BRSET"],
        "name": "BRSET",
        "representative_words": ["BRSET"],
        "website": "https://physionet.org/content/brazilian-ophthalmological/1.0.1/"
    }




    process_repos_file(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)
