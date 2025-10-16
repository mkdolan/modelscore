#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""
HuggingFace Repository Cards Query Script

This script queries HuggingFace repository cards for model information
and saves the results as JSON files in the model_scores folder.

Usage Examples:
    python3 hf_cards.py meta-llama/Llama-4-Scout-17B-16E-Instruct
    python3 hf_cards.py google-bert/bert-base-uncased
    python3 hf_cards.py meta-llama/Llama-4-Scout-17B-16E-Instruct google-bert/bert-base-uncased microsoft/DialoGPT-medium

The script will create JSON files in the model_scores folder with filenames
based on the model names (slashes replaced with underscores) containing
all available repository card data.
"""

import json
import os
import sys
from typing import Optional, Dict, Any
from huggingface_hub import RepoCard


def query_repository_card(model_name: str) -> Optional[Dict[Any, Any]]:
    """
    Query the HuggingFace repository card for model information.
    
    Args:
        model_name: The HuggingFace model ID (e.g., "meta-llama/Llama-4-Scout-17B-16E-Instruct")
        
    Returns:
        Dictionary containing repository card information, or None if query failed
    """
    try:
        print(f"Querying HuggingFace repository card: {model_name}")
        
        # Load the repository card
        card = RepoCard.load(model_name)
        
        # Extract all available data from the card
        card_data = {
            "model_name": model_name,
            "card_data": card.data.to_dict() if card.data else {},
            "card_text": card.text,
            "card_content": card.content,
            "metadata": {}
        }
        
        # Add metadata if available
        if hasattr(card.data, '__dict__'):
            card_data["metadata"] = card.data.__dict__
        
        print(f"Successfully retrieved repository card for model: {model_name}")
        return card_data
        
    except Exception as e:
        print(f"Error loading repository card: {e}")
        return None


def save_card_data_to_json(model_name: str, card_data: Dict[Any, Any]) -> Optional[str]:
    """
    Save repository card data to a JSON file in the model_scores folder.
    
    Args:
        model_name: The HuggingFace model ID
        card_data: Dictionary containing repository card information
        
    Returns:
        Path to the saved file, or None if save failed
    """
    try:
        # Create model_scores directory if it doesn't exist
        model_scores_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "model_scores")
        os.makedirs(model_scores_dir, exist_ok=True)
        
        # Create filename from model name (replace slashes with underscores)
        filename = model_name.replace("/", "_") + "_card.json"
        file_path = os.path.join(model_scores_dir, filename)
        
        # Save data to JSON file with pretty formatting
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(card_data, json_file, indent=2, ensure_ascii=False)
        
        print(f"Repository card data saved to: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return None


def query_and_save_card(model_name: str) -> bool:
    """
    Query HuggingFace repository card for a model and save the results as JSON.
    
    Args:
        model_name: The HuggingFace model ID
        
    Returns:
        True if successful, False otherwise
    """
    # Query the repository card data
    card_data = query_repository_card(model_name)
    
    if card_data is None:
        print(f"Failed to retrieve repository card for model: {model_name}")
        return False
    
    # Save the data to JSON
    saved_path = save_card_data_to_json(model_name, card_data)
    
    if saved_path is None:
        print(f"Failed to save repository card data for model: {model_name}")
        return False
    
    print(f"Successfully processed repository card for model: {model_name}")
    return True


def main():
    """
    Main function to handle command line arguments and process models.
    """
    if len(sys.argv) < 2:
        print("Usage: python hf_cards.py <model-name> [model-name2] [model-name3] ...")
        print("Example: python hf_cards.py meta-llama/Llama-4-Scout-17B-16E-Instruct")
        print("Example: python hf_cards.py google-bert/bert-base-uncased")
        sys.exit(1)
    
    # Process each model name provided as command line arguments
    success_count = 0
    total_count = len(sys.argv) - 1
    
    for i in range(1, len(sys.argv)):
        model_name = sys.argv[i]
        print(f"\n{'='*60}")
        print(f"Processing repository card {i}/{total_count}: {model_name}")
        print(f"{'='*60}")
        
        if query_and_save_card(model_name):
            success_count += 1
        else:
            print(f"Failed to process repository card for model: {model_name}")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Processing complete: {success_count}/{total_count} repository cards processed successfully")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
