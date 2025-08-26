import openai
import json
import re
from openai import OpenAI
from utils.path_utils import here

# Set your OpenAI API key (replace with your actual key)
api_key = "sk-xxx" # Replace with your actual token
client = OpenAI(api_key=api_key)

def check_license_violation_with_openai(dataset_record, original_info):
    """
    Use OpenAI's API to analyze a downstream dataset record against the original dataset's licensing rules.
    Returns a JSON object with two keys:
      - "has_violation": a boolean indicating if any violations exist.
      - "violations": an array of violation objects.
    
    Each violation object must have:
      - "rule": one of the following exact values:
          "non_commercial", "sharealike", "no_derivatives", "give_credit", "special_requirement"
      - "detail": a natural language explanation.
    """
    prompt = (
        "You are a dataset licensing compliance auditor. Your task is to determine whether a downstream dataset record "
        "violates the original dataset's licensing requirements. Follow these rules carefully:\n\n"
        "1. Your output must be a single valid JSON object with exactly two keys: 'has_violation' and 'violations'.\n"
        "2. 'has_violation' must be a boolean. It is true if at least one violation exists, false otherwise.\n"
        "3. 'violations' must be an array. Each element is an object with exactly two keys: 'rule' and 'detail'.\n"
        "   - 'rule' must be one of: 'non_commercial', 'sharealike', 'no_derivatives', "
        "'attribution', 'open_source', 'distribution_platform', 'naming'.\n"
        "   - 'detail' must be a clear natural-language explanation explicitly referencing the original dataset’s requirements.\n"
        "4. If no violations are found, return: {\"has_violation\": false, \"violations\": []}.\n\n"
        "Original dataset licensing requirements:\n"
        f"{json.dumps(original_info, indent=2)}\n\n"
        "Downstream dataset record:\n"
        f"{json.dumps(dataset_record, indent=2)}\n\n"
        "Check compliance against the following rules:\n"
        "a. non_commercial: If true, the downstream license must explicitly prohibit commercial use. "
        "If the downstream dataset license allows commercial use, is missing, or is unclear, this is a violation.\n"
        "b. sharealike: If true, the downstream license must be identical to the original license. "
        "Any deviation (even more permissive) is a violation.\n"
        "c. no_derivatives: If true, the downstream dataset must not create or distribute derivative works. "
        "If modifications, extensions, or derivatives are indicated, this is a violation.\n"
        "d. attribution: If true, the downstream dataset must provide attribution, including: "
        "the creator's name, attribution parties, a copyright notice, "
        "a license notice, a disclaimer notice, and a link to the original material. "
        "Missing any of these is a violation.\n"
        "e. open_source: If true, the downstream dataset or related code/derivatives must be released under an open-source license. "
        "If it is closed-source, missing, or unclear, this is a violation.\n"
        "f. distribution_platform: If true, redistribution must occur on the specified platforms (e.g. Physionet). "
        "If it is distributed elsewhere, this is a violation.\n\n"
        "Return only the JSON object. Do not include explanations or text outside of the JSON."
    )
    
    
    try:
        # print(prompt)
        # exit()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a licensing compliance expert."},
                {"role": "user", "content": prompt}
            ],
        )
        answer = response.choices[0].message.content.strip()
        
        if not answer:
            print(f"Empty response from OpenAI API for dataset: {dataset_record.get('id')}")
            return {"has_violation": False, "violations": []}
        
        # Extract JSON content if the answer is wrapped in markdown code blocks.
        json_str = ""
        match = re.search(r"```json\s*(.*?)\s*```", answer, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = answer.strip()
        
        try:
            result = json.loads(json_str)
        except json.JSONDecodeError as json_err:
            print("Failed to parse JSON response. Extracted content was:")
            print(json_str)
            print("JSONDecodeError:", json_err)
            return {"has_violation": False, "violations": []}
        
        # Validate that the result is a dict with the expected keys.
        if not isinstance(result, dict) or "has_violation" not in result or "violations" not in result:
            print("Unexpected JSON format. Expected a dict with keys 'has_violation' and 'violations'. Got:", result)
            return {"has_violation": False, "violations": []}
        
        return result
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return {"has_violation": False, "violations": []}

def analyze_downstream_usage(downstream_datasets, original_info):
    """
    Loop over each downstream dataset record marked as downstream usage, use OpenAI to determine licensing violations,
    and return a list of updated dataset records that include a 'violations' field and a boolean 'has_violation' field.
    """
    updated_records = []
    total = len(downstream_datasets)
    for idx, dataset_record in enumerate(downstream_datasets, 1):
        # Only process records that are marked as downstream usage.
        if not dataset_record.get("downstream_usage", {}).get("is_downstream", False):
            continue

        print(f"Processing record {idx}/{total}: {dataset_record.get('id')}")

        violation_info = check_license_violation_with_openai(dataset_record, original_info)
        # Add the violation info to the dataset record.
        dataset_record["has_violation"] = violation_info.get("has_violation", False)
        dataset_record["violations"] = violation_info.get("violations", [])
        updated_records.append(dataset_record)
    return updated_records

def save_violations_to_file(updated_records, filename="violations.json"):
    """
    Save the updated dataset records (with violation info) to a JSON file.
    """
    with open(here(filename), "w") as f:
        json.dump(updated_records, f, indent=4)

def check_huggingface(KEYWORD):
    # Load the original dataset licensing info from file.
    # KEYWORD = "BRSET"  # Example keyword
    with open(here(f"extracted_dataset_info_with_license_analysis_{KEYWORD}.json"), "r") as f:
        original_info = json.load(f)
    
    # Load the downstream datasets from file.
    with open(here(f"final_processed_huggingface_{KEYWORD}.json"), "r") as f:
        downstream_datasets = json.load(f)
    
    # Analyze each downstream dataset for licensing compliance violations.
    updated_records = analyze_downstream_usage(downstream_datasets, original_info)
    
    # Save the updated records (with added 'has_violation' and 'violations' fields) to a file.
    save_violations_to_file(updated_records, f"violations_huggingface_{KEYWORD}.json")
    print(f"Analysis complete. Updated records saved to violations_huggingface_{KEYWORD}.json")
    
    # Optionally, print the first updated record for inspection.
    if updated_records:
        # print("First updated record:")
        # print(json.dumps(updated_records[0], indent=2))
        print(f"Total downstream records processed: {len(updated_records)}")
    else:
        print("No downstream records processed.")

if __name__ == "__main__":
    KEYWORD = "BRSET"  # Example keyword
    check_huggingface(KEYWORD)
