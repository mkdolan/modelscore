#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Query HuggingFace API for user information and append to Excel
"""

import requests
import csv
from pathlib import Path
from typing import Dict, Any, Optional
from excel_manager import ExcelManager

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

def append_user_info_to_excel(user_info: Dict[str, Any], excel_manager: ExcelManager, 
                             row_number: int, user_name: str) -> None:
    """
    Append user information to the Excel file as a new tab
    
    Args:
        user_info (dict): User information from the API
        excel_manager (ExcelManager): Excel manager instance
        row_number (int): Row number from the model list map file
        user_name (str): The username that was queried
    """
    if not user_info:
        return
    
    # Create tab name
    tab_name = f"{row_number}-HF-user"
    
    # Create row-based data structure
    user_data = []
    
    # Add the User Name row first
    user_data.append({"Label": "User Name", "Value": user_name})

    # Add each key-value pair as a separate row
    for key, value in user_info.items():
        user_data.append({"Label": key, "Value": value})
    
    # Use Excel manager to create the tab
    excel_manager.create_tab_from_csv_data(tab_name, user_data)

def append_user_info_to_csv(user_info, csv_file_path):
    """
    Append user information to the CSV file
    
    DEPRECATED: Use append_user_info_to_excel instead.
    
    Args:
        user_info (dict): User information from the API
        csv_file_path (str): Path to the CSV file
    """
    if not user_info:
        return
        
    # Check if CSV file exists
    file_exists = Path(csv_file_path).exists()
    
    # Create row-based data structure
    user_data = []
    
    # Add each key-value pair as a separate row
    for key, value in user_info.items():
        user_data.append({"Label": key, "Value": value})
    
    # Open CSV file in append mode
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        # Define fieldnames for the row-based format
        fieldnames = ["Label", "Value"]
        
        # Create CSV writer
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file doesn't exist
        if not file_exists:
            writer.writeheader()
            
        # Write each row of user info
        for row in user_data:
            writer.writerow(row)

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