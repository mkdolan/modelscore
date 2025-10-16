#!/usr/bin/env python3
"""
Main entry point for the Python project
"""

from huggingface_hub import HfApi
import os
import csv
import sys
import requests

def main():
    """Main function"""
    model_name = None
    
    if len(sys.argv) > 1:
        model_name = sys.argv[1]

    if model_name is None or not isinstance(model_name, str) or model_name.strip() == "":
        model_name = "google-bert/bert-base-uncased"
    
    print(f"Querying model: {model_name}")
    
    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # Query specific model information
        info = api.model_info(model_name)
        print(info.modelId, info.sha)
        
        # Extract owner from model name (first part before slash)
        owner_name = model_name.split('/')[0]
        print(f"Querying owner information for: {owner_name}")

        #api.user_info(owner_name)
        #print(user_info)
        
        # Query owner information using direct API call
        owner_info = None
        try:
            # Try user endpoint first
            api_url = f"https://huggingface.co/api/users/{owner_name}/overview"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                owner_info = response.json()
                print(f"Owner found: {owner_info.get('name', owner_name)}")
            elif response.status_code == 404:
                # Try organization endpoint
                org_url = f"https://huggingface.co/api/orgs/{owner_name}"
                org_response = requests.get(org_url)
                print(f"Could not fetch user information: HTTP {org_response.status_code}")
            else:
                print(f"Could not fetch user information: HTTP {response.status_code}")
        except Exception as owner_error:
            print(f"Could not fetch user information: {owner_error}")
            owner_info = None
        
        # Export all available information to CSV
        with open('model_info.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['Key', 'Value'])
            # Write all key-value pairs from model info
            for key, value in info.__dict__.items():
                writer.writerow([key, value])
            
            # Add separator for owner information
            writer.writerow(['', ''])
            writer.writerow(['OWNER_INFORMATION', ''])
            
            # Write owner information if available
            if owner_info:
                for key, value in owner_info.items():
                    writer.writerow([f'owner_{key}', value])
            else:
                writer.writerow(['owner_error', 'Could not fetch detailed owner information via API'])
                # Add basic owner info from model data
                writer.writerow(['owner_username', owner_name])
                writer.writerow(['owner_from_model_author', info.author])
                writer.writerow(['note', 'Detailed owner information requires authentication or different API access'])
        
        print("Model and owner information exported to model_info.csv")
        
    except Exception as e:
        print(f"Error querying Hugging Face: {e}")

if __name__ == "__main__":
    main()