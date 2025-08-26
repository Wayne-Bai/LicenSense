import requests
import re
import html
from typing import Union, Dict, Any
from openai import OpenAI
import json
import os
from utils.path_utils import here

# Set your OpenAI API key (replace with your actual key)
api_key = "sk-xxx" # Replace with your actual token
client = OpenAI(api_key=api_key)

def html_to_text(raw_html: str) -> str:
    """Convert raw HTML string to plain text (simple regex cleanup)."""
    # Remove comments
    text = re.sub(r"<!--.*?-->", "", raw_html, flags=re.DOTALL)
    # Remove script/style/noscript blocks
    text = re.sub(r"<(script|style|noscript).*?>.*?</\1>", "", text, flags=re.DOTALL|re.IGNORECASE)
    # Replace <br> and block closings with newlines
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|section|article|tr|td|th|li|ul|ol|h\d)>", "\n", text, flags=re.IGNORECASE)
    # Remove all other tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Normalize whitespace
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # drop empty lines
    return "\n".join(lines)

def extract_license_text(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    raw_html = response.text
    text = html_to_text(raw_html)
    return text

def extract_json_from_text(data: str) -> Union[Dict[str, Any], str]:
    """
    Extracts JSON from a given string by looking for a code block delimited by ```json ... ```.
    If not found, attempts to parse the entire text.
    
    Args:
        data (str): The text that may contain JSON.
    
    Returns:
        Dict[str, Any] or str: The parsed JSON as a dictionary, or an error message.
    """
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, data, re.DOTALL)
    if match:
        json_text = match.group(1)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            return f"JSON decoding error: {e}"
    else:
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return "No valid JSON found in input text."

def detect_license_rules(license_text: str) -> Union[Dict[str, bool], str]:
    """
    Uses the OpenAI API to analyze the license text for specific rules:
      1. Non-commercial
      2. ShareAlike
      3. No Derivatives
      4. Give Credit
      5. Open Source
      6. Special Requirement
      
    Returns a dictionary with boolean values for each rule.
    """
    prompt = (
        "You are an assistant specialized in analyzing dataset licenses. "
        "Analyze the license text below and return ONLY valid JSON with these keys: "
        "non_commercial, sharealike, no_derivatives, attribution, open_source, distribution_platform, naming. "
        "Each value must be true or false. If a rule is not mentioned, return false.\n\n"
        "Interpretation rules:\n"
        "- Non-commercial (NC): return true if the license prohibits commercial use OR restricts use to "
        "  non-commercial contexts such as 'research-only', 'educational use only', 'academic use only', "
        "  'scientific research and no other', or 'non-profit use only'. These phrases count as NC even if the word "
        "  'commercial' is not used.\n"
        "- Share-Alike (SA): true if derivatives must use the same license terms.\n"
        "- No Derivatives (ND): true if modifications/derivatives are not allowed.\n"
        "- Attribution (BY): true if credit/citation is required.\n"
        "- Open Source (OS): true if the license requires downstream users to release code or derivatives openly.\n"
        "- Distribution Platform (DP): true if redistribution must occur on specified platforms or channels only.\n"
        "- Naming: true if the license requires specific naming for derivative datasets.\n\n"
        "Return JSON exactly like:\n"
        "{\n"
        "  \"non_commercial\": true/false,\n"
        "  \"sharealike\": true/false,\n"
        "  \"no_derivatives\": true/false,\n"
        "  \"attribution\": true/false,\n"
        "  \"open_source\": true/false,\n"
        "  \"distribution_platform\": true/false,\n"
        "  \"naming\": true/false\n"
        "}\n\n"
        "License text:\n"
        f"{license_text}\n\n"
        "JSON:"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that analyzes license texts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.0
        )
        output_text = response.choices[0].message.content
        result = extract_json_from_text(output_text)
        return result
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def extract_license_terms(license):
    """
    This function extracts license terms from the dataset information.
    It can be customized to extract specific license terms as needed.
    """

    # Get absolute path of the current script
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # json_path = os.path.join(current_dir, "license_terms.json")

    # with open(json_path, "r", encoding="utf-8") as f:
    with open(here() + "/license_extract/license_terms.json", "r", encoding="utf-8") as f:
        existing_license_terms = json.load(f)
    existing_licenses = list(existing_license_terms.keys())

    if license in existing_licenses:
        result = {
            "license": license,
            "license_analysis": existing_license_terms[license]
        }
        return result

    if license.startswith("http"):
        license = extract_license_text(license)
    
    license_term = detect_license_rules(license)
    result = {
        "license": "Custom License",
        "license_analysis": license_term
    }
    return result

if __name__ == "__main__":
    # Example usage
    license = "CC-BY-NC-ND-4.0"
    license_terms = extract_license_terms(license)
    print(license_terms)  # Output the extracted license terms
    
    
