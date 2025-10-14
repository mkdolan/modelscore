#!/usr/bin/env python3
"""
Query HuggingFace API for user information and append to CSV
"""

import requests
import csv
from pathlib import Path

def query_user_overview(user_name):
    """
    Query the HuggingFace API for user overview information
    
    Args:
        user_name (str): The username to query
        
    Returns:
        dict: JSON response from the API
    """
    url = f"https://huggingface.co/api/users/{user_name}/overview"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying Hugging Face API: {e}")
        return None

def append_user_info_to_csv(user_info, csv_file_path):
    """
    Append user information to the CSV file
    
    Args:
        user_info (dict): User information from the API
        csv_file_path (str): Path to the CSV file
    """
    if not user_info:
        return
        
    # Check if CSV file exists
    file_exists = Path(csv_file_path).exists()
    
    # Open CSV file in append mode
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        # Get all keys from user_info to use as fieldnames
        fieldnames = list(user_info.keys())
        
        # Create CSV writer
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
            
        # Write user info
        writer.writerow(user_info)

def main():
    """Main function"""
    # This would typically be passed as an argument
    user_name = "julien-c"  # Example user name
    
    print(f"Querying user overview for: {user_name}")
    
    # Query user information
    user_info = query_user_overview(user_name)
    
    if user_info:
        print("User information retrieved successfully")
        print(user_info)
        
        # Append to CSV file
        append_user_info_to_csv(user_info, 'model_info.csv')
        print("User information appended to model_info.csv")
    else:
        print("Failed to retrieve user information")

if __name__ == "__main__":
    main()