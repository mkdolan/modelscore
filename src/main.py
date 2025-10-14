#!/usr/bin/env python3
"""
Main entry point for the Python project
"""

import sys
from model_query import get_model_info, export_model_info_to_csv, query_and_export_model
from user_query import query_user_overview, append_user_info_to_csv

def main():
    """Main function"""
    model_name = None
    
    if len(sys.argv) > 1:
        model_name = sys.argv[1]

    if model_name is None or not isinstance(model_name, str) or model_name.strip() == "":
        model_name = "google-bert/bert-base-uncased"
    
    print(f"Querying model: {model_name}")    
    try:
        info = get_model_info(model_name)
        print(info.modelId, info.sha)
        
        # Extract owner from model name (first part before slash)
        owner_name = model_name.split('/')[0]
        print(f"Querying owner information for: {owner_name}")

        export_model_info_to_csv(info, '../model_scores/model_info.csv')
        print("Model information exported to model_info.csv")
        
        # Query user/owner information and append to CSV
        user_info = query_user_overview(owner_name)
        if user_info:
            print("Owner information retrieved successfully")
            append_user_info_to_csv(user_info, 'model_info.csv')
            print("Owner information appended to model_info.csv")
        else:
            print("Failed to retrieve owner information")
        
    except Exception as e:
        print(f"Error querying Hugging Face: {e}")

if __name__ == "__main__":
    main()