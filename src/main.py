#!/usr/bin/env python3
"""
Main entry point for the Python project
"""

from huggingface_hub import HfApi
import os
import csv

def main():
    """Main function"""
    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # Query specific model information
        info = api.model_info("bert-base-uncased")
        print(info.modelId, info.sha)
        
        # Export all available information to CSV
        with open('model_info.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['Key', 'Value'])
            # Write all key-value pairs
            for key, value in info.__dict__.items():
                writer.writerow([key, value])
        
        print("Model information exported to model_info.csv")
        
    except Exception as e:
        print(f"Error querying Hugging Face: {e}")

if __name__ == "__main__":
    main()
