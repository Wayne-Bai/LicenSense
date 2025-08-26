from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import json
from utils.path_utils import here

from coarse_search.crawl_kaggle import search_kaggle
from coarse_search.crawl_huggingface import search_huggingface
from coarse_search.crawl_github import search_github

from data_process.process_kaggle import clean_kaggle_data
from data_process.process_huggingface import clean_huggingface_data
from data_process.process_github import clean_github_data

from fine_filter.fine_filter_kaggle import filter_kaggle
from fine_filter.fine_filter_huggingface import filter_huggingface
from fine_filter.fine_filter_github import filter_github

from license_extract.license_term_extract import extract_license_terms

from compliance_check.compliance_kaggle import check_kaggle
from compliance_check.compliance_huggingface import check_huggingface
from compliance_check.compliance_github import check_github
from compliance_check.crawl_citation import crawl_citation
from compliance_check.compliance_open_source import check_open_source


llm = ChatOpenAI(model="gpt-4o")

OPENAI_API_KEY = "sk-xxx" # Replace with your actual API key

class State(TypedDict):
    RepresentativeTerm: str
    Title: str
    Website: str
    Keywords: str
    Description: str
    Citation: str
    License: str

# CORSE SEARCH: Kaggle, Huggingface, Github
def coarse_search_kaggle(State):
    search_keyword = State["RepresentativeTerm"]
    search_kaggle(search_keyword)

def coarse_search_huggingface(State):
    search_keyword = State["RepresentativeTerm"]
    search_huggingface(search_keyword)

def coarse_search_github(State):
    search_keyword = State["RepresentativeTerm"]
    search_github(search_keyword)

# DATA PROCESS: Clean coarse searched data from Kaggle, Huggingface, Github
    
def process_kaggle(State):
    representative_term = State["RepresentativeTerm"]
    clean_kaggle_data(representative_term)

def process_huggingface(State):
    representative_term = State["RepresentativeTerm"]
    clean_huggingface_data(representative_term)

def process_github(State):
    representative_term = State["RepresentativeTerm"]
    clean_github_data(representative_term)

# FINE FILTER: Kaggle, Huggingface, Github

def fine_filter_kaggle(State):
    representative_term = State["RepresentativeTerm"]
    INPUT_FILE = f"processed_kaggle_{representative_term}.json"
    OUTPUT_FILE = f"final_processed_kaggle_{representative_term}.json"

    dataset_info = {
        "title": State["Title"],
        "topics": State['Description'],
        "name": State["RepresentativeTerm"],
        "representative_term": State["RepresentativeTerm"],
        "keywords": State["Keywords"],
        "website": State["Website"],
    }

    filter_kaggle(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)

def fine_filter_huggingface(State):
    representative_term = State["RepresentativeTerm"]
    INPUT_FILE = f"processed_huggingface_datasets_{representative_term}.json"
    OUTPUT_FILE = f"final_processed_datasets_{representative_term}.json"

    dataset_info = {
        "title": State["Title"],
        "topics": State['Description'],
        "name": State["RepresentativeTerm"],
        "representative_term": State["RepresentativeTerm"],
        "keywords": State["Keywords"],
        "website": State["Website"],
    }
    filter_huggingface(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)

def fine_filter_github(State):
    representative_term = State["RepresentativeTerm"]
    INPUT_FILE = f"processed_github_repos_{representative_term}.json"
    OUTPUT_FILE = f"final_processed_repos_{representative_term}.json"

    dataset_info = {
        "title": State["Title"],
        "topics": State['Description'],
        "name": State["RepresentativeTerm"],
        "representative_term": State["RepresentativeTerm"],
        "keywords": State["Keywords"],
        "website": State["Website"],
    }
    filter_github(INPUT_FILE, OUTPUT_FILE, OPENAI_API_KEY, dataset_info)

# Extract License Terms:
def original_license_formalization(State):
    title = State["Title"]
    license_text = State["License"]
    license_terms = extract_license_terms(license_text)
    license = license_terms["license"]
    license_analysis = license_terms["license_analysis"]
    representative_term = State["RepresentativeTerm"]
    website = State["Website"]
    citation = State["Citation"]

    output_file = f"extracted_dataset_info_with_license_analysis_{representative_term}.json"

    processed_data = {
        "title": title,
        "license": license,
        "representative word": representative_term,
        "website": website,
        "citation": citation,
        "license_analysis": license_analysis
    }

    with open(here(output_file), "w", encoding="utf-8") as f:
            json.dump(processed_data, f, indent=2)
    print(f"Processed and saved results to {output_file}")

# Compliance Check with Kaggle, Huggingface, Github
def compliance_kaggle(State):
    representative_term = State["RepresentativeTerm"]
    check_kaggle(representative_term)

def compliance_huggingface(State):
    representative_term = State["RepresentativeTerm"]
    check_huggingface(representative_term)

def compliance_github(State):
    representative_term = State["RepresentativeTerm"]
    check_github(representative_term)

def compliance_citation(State):
    representative_term = State["RepresentativeTerm"]
    title = State["Title"]

    with open(here(f"extracted_dataset_info_with_license_analysis_{representative_term}.json"), "r") as f:
        original_info = json.load(f)
    
    if original_info["license_analysis"]["open_source"]:
        crawl_citation(representative_term, title)
        check_open_source(representative_term)

builder = StateGraph(State)
builder.add_node("Corse Search Kaggle", coarse_search_kaggle)
builder.add_node("Corse Search Huggingface", coarse_search_huggingface)
builder.add_node("Corse Search Github", coarse_search_github)
builder.add_node("Process Kaggle", process_kaggle)
builder.add_node("Process Huggingface", process_huggingface)
builder.add_node("Process Github", process_github)
builder.add_node("Fine Filter Kaggle", fine_filter_kaggle)
builder.add_node("Fine Filter Huggingface", fine_filter_huggingface)
builder.add_node("Fine Filter Github", fine_filter_github)
builder.add_node("Original License Formalization", original_license_formalization)
builder.add_node("Compliance Kaggle", compliance_kaggle)
builder.add_node("Compliance Huggingface", compliance_huggingface)
builder.add_node("Compliance Github", compliance_github)
builder.add_node("Compliance Open Source", compliance_citation)

# builder.add_edge(START, "Corse Search Kaggle")
# builder.add_edge(START, "Corse Search Huggingface")
# builder.add_edge(START, "Corse Search Github")
# builder.add_edge(START, "Original License Formalization")

# builder.add_edge("Corse Search Kaggle", "Process Kaggle")
# builder.add_edge("Corse Search Huggingface", "Process Huggingface")
# builder.add_edge("Corse Search Github", "Process Github")

# builder.add_edge("Process Kaggle", "Fine Filter Kaggle")
# builder.add_edge("Process Huggingface", "Fine Filter Huggingface")
# builder.add_edge("Process Github", "Fine Filter Github")

# builder.add_edge("Fine Filter Kaggle", "Compliance Kaggle")
# builder.add_edge("Fine Filter Huggingface", "Compliance Huggingface")
# builder.add_edge("Fine Filter Github", "Compliance Github")
# builder.add_edge("Original License Formalization", "Compliance Open Source")

# builder.add_edge("Compliance Kaggle", END)
# builder.add_edge("Compliance Huggingface", END)
# builder.add_edge("Compliance Github", END)
# builder.add_edge("Compliance Open Source", END)


builder.add_edge(START, "Original License Formalization")

builder.add_edge("Original License Formalization", "Compliance Open Source")

builder.add_edge("Compliance Open Source", END)

graph = builder.compile()


