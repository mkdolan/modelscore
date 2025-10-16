#!/usr/bin/env python3
"""
HuggingFace Web API Query Script

This script queries the HuggingFace web API for model information
and saves the results as JSON files in the model_scores folder.

Usage Examples:
    python3 hf_webquery.py meta-llama/Llama-4-Scout-17B-16E-Instruct
    python3 hf_webquery.py google-bert/bert-base-uncased
    python3 hf_webquery.py meta-llama/Llama-4-Scout-17B-16E-Instruct google-bert/bert-base-uncased microsoft/DialoGPT-medium

The script will create JSON files in the model_scores folder with filenames
based on the model names (slashes replaced with underscores).
"""

import requests
import json
import os
import sys
from typing import Optional, Dict, Any
from urllib.parse import quote


def query_huggingface_model(model_name: str) -> Optional[Dict[Any, Any]]:
    """
    Query the HuggingFace web API for model information.
    
    Args:
        model_name: The HuggingFace model ID (e.g., "meta-llama/Llama-4-Scout-17B-16E-Instruct")
        
    Returns:
        Dictionary containing model information, or None if query failed
    """
    # Construct the API URL
    api_url = f"https://huggingface.co/api/models/{quote(model_name)}"
    
    try:
        print(f"Querying HuggingFace API: {api_url}")
        
        # Make the API request
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse JSON response
        model_data = response.json()
        
        print(f"Successfully retrieved data for model: {model_name}")
        return model_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def save_model_data_to_json(model_name: str, model_data: Dict[Any, Any]) -> Optional[str]:
    """
    Save model data to a JSON file in the model_scores folder.
    
    Args:
        model_name: The HuggingFace model ID
        model_data: Dictionary containing model information
        
    Returns:
        Path to the saved file, or None if save failed
    """
    try:
        # Create model_scores directory if it doesn't exist
        model_scores_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model_scores")
        os.makedirs(model_scores_dir, exist_ok=True)
        
        # Create filename from model name (replace slashes with underscores)
        filename = model_name.replace("/", "_") + ".json"
        file_path = os.path.join(model_scores_dir, filename)
        
        # Save data to JSON file with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(model_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"Model data saved to: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return None


def query_and_save_model(model_name: str) -> bool:
    """
    Query HuggingFace API for a model and save the results as JSON.
    
    Args:
        model_name: The HuggingFace model ID
        
    Returns:
        True if successful, False otherwise
    """
    # Query the model data
    model_data = query_huggingface_model(model_name)
    
    if model_data is None:
        print(f"Failed to retrieve data for model: {model_name}")
        return False
    
    # Save the data to JSON
    saved_path = save_model_data_to_json(model_name, model_data)
    
    if saved_path is None:
        print(f"Failed to save data for model: {model_name}")
        return False
    
    print(f"Successfully processed model: {model_name}")
    return True


def main():
    """
    Main function to handle command line arguments and process models.
    """
    if len(sys.argv) < 2:
        print("Usage: python hf_webquery.py <model-name> [model-name2] [model-name3] ...")
        print("Example: python hf_webquery.py meta-llama/Llama-4-Scout-17B-16E-Instruct")
        sys.exit(1)
    
    # Process each model name provided as command line arguments
    success_count = 0
    total_count = len(sys.argv) - 1
    
    for i in range(1, len(sys.argv)):
        model_name = sys.argv[i]
        print(f"\n{'='*60}")
        print(f"Processing model {i}/{total_count}: {model_name}")
        print(f"{'='*60}")
        
        if query_and_save_model(model_name):
            success_count += 1
        else:
            print(f"Failed to process model: {model_name}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Processing complete: {success_count}/{total_count} models processed successfully")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
