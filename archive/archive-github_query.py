#!/usr/bin/env python3
"""
Query GitHub API for repository information and save as JSON
"""

import requests
import json
import csv
from pathlib import Path
from typing import Optional, Dict, Any


def query_github_repository(gh_model_name: str, token: Optional[str] = None) -> Optional[Dict[Any, Any]]:
    """
    Query the GitHub API for repository information
    
    Args:
        gh_model_name (str): The GitHub repository name in format "owner/repo"
        token (str, optional): GitHub personal access token for higher rate limits
        
    Returns:
        dict: JSON response from the GitHub API, or None if error
    """
    url = f"https://api.github.com/repos/{gh_model_name}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ModelScore-GitHub-Query"
    }
    
    # Add authorization header if token is provided
    if token:
        headers["Authorization"] = f"token {token}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying GitHub API: {e}")
        return None


def get_additional_github_info(gh_model_name: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Get additional GitHub repository information (commits, issues, etc.)
    
    Args:
        gh_model_name (str): The GitHub repository name in format "owner/repo"
        token (str, optional): GitHub personal access token for higher rate limits
        
    Returns:
        dict: Additional repository information
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ModelScore-GitHub-Query"
    }
    
    if token:
        headers["Authorization"] = f"token {token}"
    
    additional_info = {}
    
    # Get repository statistics
    try:
        stats_url = f"https://api.github.com/repos/{gh_model_name}/stats/contributors"
        response = requests.get(stats_url, headers=headers)
        if response.status_code == 200:
            additional_info["contributors_stats"] = response.json()
    except Exception as e:
        print(f"Error getting contributor stats: {e}")
    
    # Get repository topics
    try:
        topics_url = f"https://api.github.com/repos/{gh_model_name}/topics"
        response = requests.get(topics_url, headers=headers)
        if response.status_code == 200:
            additional_info["topics"] = response.json()
    except Exception as e:
        print(f"Error getting topics: {e}")
    
    # Get repository languages
    try:
        languages_url = f"https://api.github.com/repos/{gh_model_name}/languages"
        response = requests.get(languages_url, headers=headers)
        if response.status_code == 200:
            additional_info["languages"] = response.json()
    except Exception as e:
        print(f"Error getting languages: {e}")
    
    # Get repository releases
    try:
        releases_url = f"https://api.github.com/repos/{gh_model_name}/releases"
        response = requests.get(releases_url, headers=headers)
        if response.status_code == 200:
            releases = response.json()
            additional_info["latest_release"] = releases[0] if releases else None
            additional_info["total_releases"] = len(releases)
    except Exception as e:
        print(f"Error getting releases: {e}")
    
    return additional_info




def save_github_info_to_json(github_info: Dict[str, Any], json_file_path: str) -> None:
    """
    Save GitHub repository information to a JSON file
    
    Args:
        github_info (dict): GitHub repository information
        json_file_path (str): Path to the JSON file
    """
    if not github_info:
        return
    
    # Check if JSON file exists to determine if we should append or create new
    file_exists = Path(json_file_path).exists()
    
    if file_exists:
        # Read existing JSON data
        try:
            with open(json_file_path, 'r', encoding='utf-8') as jsonfile:
                existing_data = json.load(jsonfile)
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or empty, start fresh
            existing_data = {"repositories": []}
    else:
        # Create new structure
        existing_data = {"repositories": []}
    
    # Ensure the structure has a repositories list
    if not isinstance(existing_data, dict) or "repositories" not in existing_data:
        existing_data = {"repositories": []}
    
    # Add new repository information
    existing_data["repositories"].append(github_info)
    
    # Write back to JSON file with pretty formatting
    with open(json_file_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(existing_data, jsonfile, indent=2, ensure_ascii=False)


def main():
    """Main function for GitHub query"""
    import sys
    
    # Get GitHub model name from command line argument
    if len(sys.argv) > 1:
        gh_model_name = sys.argv[1]
    else:
        # Default repository for testing
        gh_model_name = "huggingface/transformers"
    
    # Optional: Get GitHub token from environment variable
    import os
    token = os.getenv('GITHUB_TOKEN')
    
    print(f"Querying GitHub repository: {gh_model_name}")
    
    # Query basic repository information
    repo_info = query_github_repository(gh_model_name, token)
    
    if repo_info:
        print("Repository information retrieved successfully")
        
        # Get additional repository information
        print("Fetching additional repository information...")
        additional_info = get_additional_github_info(gh_model_name, token)
        
        # Combine all information
        all_info = {**repo_info, **additional_info}
        
        # Save to JSON file
        save_github_info_to_json(all_info, 'GH_response.json')
        print("GitHub repository information saved to GH_response.json")
        
        # Print some key information
        print(f"Repository: {repo_info.get('full_name', 'N/A')}")
        print(f"Description: {repo_info.get('description', 'N/A')}")
        print(f"Stars: {repo_info.get('stargazers_count', 'N/A')}")
        print(f"Forks: {repo_info.get('forks_count', 'N/A')}")
        print(f"Language: {repo_info.get('language', 'N/A')}")
        print(f"Created: {repo_info.get('created_at', 'N/A')}")
        print(f"Updated: {repo_info.get('updated_at', 'N/A')}")
        
    else:
        print("Failed to retrieve repository information")


if __name__ == "__main__":
    main()
