#!/usr/bin/env python3
"""
Main entry point for the Python project
"""

import sys
from pathlib import Path
from hf_model_query import get_model_info, export_model_info_to_csv, query_and_export_model
from hf_user_query import query_user_overview, append_user_info_to_csv
from gh_sec2 import query_github_security

def read_model_list(file_path: str = "model_list_map.txt"):
    """Read and parse the model list from the specified file.
    
    Args:
        file_path: Path to the model list file
        
    Returns:
        List of tuples containing (hf_model_name, github_repo_name)
    """
    models = []
    model_list_path = Path(__file__).parent / file_path
    
    try:
        with open(model_list_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse the line: HuggingFace Name, GitHub org/repo
                parts = line.split(',')
                if len(parts) != 2:
                    print(f"Warning: Skipping malformed line {line_num}: {line}")
                    continue
                
                hf_name = parts[0].strip()
                github_repo = parts[1].strip()
                models.append((hf_name, github_repo))
                
    except FileNotFoundError:
        print(f"Error: Model list file not found: {model_list_path}")
        return []
    except Exception as e:
        print(f"Error reading model list file: {e}")
        return []
    
    return models

def process_model(hf_model_name: str, github_repo: str):
    """Process a single model by querying HuggingFace and GitHub APIs.
    
    Args:
        hf_model_name: HuggingFace model name for HF API queries
        github_repo: GitHub repository name for GitHub API queries
    """
    print(f"\n{'='*60}")
    print(f"Processing model: {hf_model_name}")
    print(f"GitHub repo: {github_repo}")
    print(f"{'='*60}")
    
    try:
        # Query HuggingFace model information
        print(f"Querying HuggingFace model: {hf_model_name}")
        info = get_model_info(hf_model_name)
        print(f"Model ID: {info.modelId}, SHA: {info.sha}")
        
        # Extract owner from HuggingFace model name (first part before slash)
        owner_name = hf_model_name.split('/')[0]
        print(f"Querying HuggingFace owner information for: {owner_name}")

        # Export model info to CSV
        csv_path = f'../model_scores/{owner_name}_model_info.csv'
        export_model_info_to_csv(info, csv_path)
        print(f"Model information exported to {csv_path}")
        
        # Query user/owner information and append to CSV
        user_info = query_user_overview(owner_name)
        if user_info:
            print("HuggingFace owner information retrieved successfully")
            append_user_info_to_csv(user_info, csv_path)
            print("Owner information appended to CSV")
        else:
            print("Failed to retrieve HuggingFace owner information")
        
        # Query GitHub security information
        print(f"Querying GitHub security information for repository: {github_repo}")
        try:
            # Parse owner/repo from github_repo (format: "owner/repo")
            if '/' in github_repo:
                owner, repo = github_repo.split('/', 1)
                security_csv_path = query_github_security(owner, repo)
                print(f"GitHub security information exported to {security_csv_path}")
            else:
                print(f"Warning: GitHub repository name '{github_repo}' doesn't contain owner/repo format")
        except Exception as e:
            print(f"Error querying GitHub security for {github_repo}: {e}")
        
    except Exception as e:
        print(f"Error processing model {hf_model_name}: {e}")

def main():
    """Main function"""
    # Read the model list from file
    models = read_model_list()
    
    if not models:
        print("No models found in model_list_map.txt or error reading file")
        return
    
    print(f"Found {len(models)} models to process")
    
    # Process each model
    for i, (hf_model_name, github_repo) in enumerate(models, 1):
        print(f"\nProcessing model {i}/{len(models)}")
        process_model(hf_model_name, github_repo)
    
    print(f"\n{'='*60}")
    print("All models processed successfully!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()