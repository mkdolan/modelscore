#!/usr/bin/env python3
"""
Query HuggingFace API for organization information and append to CSV

Example usage:
    python3 hf_org_query.py huggingface
    python3 hf_org_query.py microsoft
    python3 hf_org_query.py meta-llama
"""

import requests
import csv
import argparse
from pathlib import Path
from excel_manager import ExcelManager

def query_org_overview(org_name):
    """
    Query the HuggingFace API for organization overview information
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/organizations/{org_name}/overview"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Hugging Face API: {e}")
        return None

def query_org_members(org_name):
    """
    Query the HuggingFace API for organization members
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/organizations/{org_name}/members"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying organization members: {e}")
        return None

def query_org_models(org_name):
    """
    Query the HuggingFace API for organization models
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/models"
    params = {"author": org_name}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying organization models: {e}")
        return None

def query_org_datasets(org_name):
    """
    Query the HuggingFace API for organization datasets
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/datasets"
    params = {"author": org_name}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying organization datasets: {e}")
        return None

def query_org_spaces(org_name):
    """
    Query the HuggingFace API for organization spaces
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/spaces"
    params = {"author": org_name}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying organization spaces: {e}")
        return None

def get_all_org_info(org_name):
    """
    Query all available organization information from HuggingFace API
    
    Args:
        org_name (str): The organization name to query
        
    Returns:
        dict: Combined organization information
    """
    print(f"Fetching organization overview for: {org_name}")
    org_overview = query_org_overview(org_name)
    
    print(f"Fetching organization members for: {org_name}")
    org_members = query_org_members(org_name)
    
    print(f"Fetching organization models for: {org_name}")
    org_models = query_org_models(org_name)
    
    print(f"Fetching organization datasets for: {org_name}")
    org_datasets = query_org_datasets(org_name)
    
    print(f"Fetching organization spaces for: {org_name}")
    org_spaces = query_org_spaces(org_name)
    
    # Combine all information into a single dictionary
    all_info = {
        "org_name": org_name,
        "overview": org_overview,
        "members": org_members,
        "models": org_models,
        "datasets": org_datasets,
        "spaces": org_spaces
    }
    
    return all_info

def append_org_info_to_excel(org_info, excel_manager, row_number):
    """
    Append organization information to the Excel file as a new tab
    
    Args:
        org_info (dict): Organization information from the API
        excel_manager (ExcelManager): Excel manager instance
        row_number (int): Row number from the model list map file
    """
    if not org_info:
        return
    
    # Create tab name
    tab_name = f"{row_number}-HF-org"
    
    # Flatten the organization info for Excel storage
    flattened_info = {}
    
    # Add basic org info
    flattened_info["org_name"] = org_info.get("org_name", "")
    
    # Add overview info if available
    if org_info.get("overview"):
        overview = org_info["overview"]
        for key, value in overview.items():
            flattened_info[f"overview_{key}"] = value
    
    # Add counts for different resource types
    flattened_info["members_count"] = len(org_info.get("members", [])) if org_info.get("members") else 0
    flattened_info["models_count"] = len(org_info.get("models", [])) if org_info.get("models") else 0
    flattened_info["datasets_count"] = len(org_info.get("datasets", [])) if org_info.get("datasets") else 0
    flattened_info["spaces_count"] = len(org_info.get("spaces", [])) if org_info.get("spaces") else 0
    
    # Convert to list format for Excel
    org_data = [flattened_info]
    
    # Use Excel manager to create the tab
    excel_manager.create_tab_from_csv_data(tab_name, org_data)

def append_org_info_to_csv(org_info, csv_file_path):
    """
    Append organization information to the CSV file
    
    DEPRECATED: Use append_org_info_to_excel instead.
    
    Args:
        org_info (dict): Organization information from the API
        csv_file_path (str): Path to the CSV file
    """
    if not org_info:
        return
        
    # Check if CSV file exists
    file_exists = Path(csv_file_path).exists()
    
    # Flatten the organization info for CSV storage
    flattened_info = {}
    
    # Add basic org info
    flattened_info["org_name"] = org_info.get("org_name", "")
    
    # Add overview info if available
    if org_info.get("overview"):
        overview = org_info["overview"]
        for key, value in overview.items():
            flattened_info[f"overview_{key}"] = value
    
    # Add counts for different resource types
    flattened_info["members_count"] = len(org_info.get("members", [])) if org_info.get("members") else 0
    flattened_info["models_count"] = len(org_info.get("models", [])) if org_info.get("models") else 0
    flattened_info["datasets_count"] = len(org_info.get("datasets", [])) if org_info.get("datasets") else 0
    flattened_info["spaces_count"] = len(org_info.get("spaces", [])) if org_info.get("spaces") else 0
    
    # Open CSV file in append mode
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        # Get all keys from flattened_info to use as fieldnames
        fieldnames = list(flattened_info.keys())
        
        # Create CSV writer
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
            
        # Write organization info
        writer.writerow(flattened_info)

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Query HuggingFace API for organization information')
    parser.add_argument('org_name', help='Organization name to query (e.g., huggingface, microsoft, meta-llama)')
    
    args = parser.parse_args()
    org_name = args.org_name
    
    print(f"Querying organization information for: {org_name}")
    
    # Query all organization information
    org_info = get_all_org_info(org_name)
    
    if org_info:
        print("Organization information retrieved successfully")
        print(f"Organization: {org_info['org_name']}")
        print(f"Members count: {org_info.get('members_count', 0)}")
        print(f"Models count: {org_info.get('models_count', 0)}")
        print(f"Datasets count: {org_info.get('datasets_count', 0)}")
        print(f"Spaces count: {org_info.get('spaces_count', 0)}")
        
        # Append to CSV file
        append_org_info_to_csv(org_info, f'../model_scores/{org_name}_org_info.csv')
        print(f"Organization information appended to {org_name}_org_info.csv")
    else:
        print("Failed to retrieve organization information")

if __name__ == "__main__":
    main()
