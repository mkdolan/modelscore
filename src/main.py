#!/usr/bin/env python3
"""
Main entry point for the Python project
"""


from huggingface_hub import HfApi
import os

def main():
    """Main function"""

    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # Query specific model information
        info = api.model_info("bert-base-uncased")
        print(info.modelId, info.sha)
        
        # Additional information about the model
        print(f"Model ID: {info.id}")
        print(f"SHA: {info.sha}")
        print(f"Downloads: {info.downloads}")
        print(f"Likes: {info.likes}")
        
    except Exception as e:
        print(f"Error querying Hugging Face: {e}")

if __name__ == "__main__":
    main()