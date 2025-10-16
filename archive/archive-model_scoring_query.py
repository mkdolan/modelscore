#!/usr/bin/env python3
"""
Model Scoring Query Tool

Queries both HuggingFace and GitHub for model information using the model mapping file
and outputs results to an Excel file with separate tabs.
"""

import csv
import os
import sys
import time
import requests
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import quote
import json
import pandas as pd
from huggingface_hub import HfApi

# GitHub API configuration
API_ROOT = "https://api.github.com"
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "User-Agent": "model-scoring-query/1.0"
})
TOKEN = os.getenv("GITHUB_TOKEN")
if TOKEN:
    SESSION.headers.update({"Authorization": f"Bearer {TOKEN}"})


def parse_model_mapping(file_path: str) -> List[Tuple[str, str]]:
    """Parse the model mapping file to extract HuggingFace and GitHub model IDs.
    
    Args:
        file_path: Path to the model_list_map.txt file
        
    Returns:
        List of tuples containing (huggingface_id, github_id)
    """
    model_mappings = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue
                
            if ',' not in line:
                print(f"Warning: Line {line_num} doesn't contain a comma, skipping: {line}")
                continue
                
            try:
                huggingface_id, github_id = line.split(',', 1)
                huggingface_id = huggingface_id.strip()
                github_id = github_id.strip()
                
                if huggingface_id and github_id:
                    model_mappings.append((huggingface_id, github_id))
                else:
                    print(f"Warning: Empty IDs on line {line_num}, skipping: {line}")
            except ValueError as e:
                print(f"Error parsing line {line_num}: {e}")
                
    return model_mappings


def _req(method: str, url: str, **kwargs) -> requests.Response:
    """HTTP wrapper with minimal rate-limit backoff."""
    for _ in range(3):
        resp = SESSION.request(method, url, timeout=30, **kwargs)
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            reset_epoch = int(resp.headers.get("X-RateLimit-Reset", "0") or 0)
            sleep_for = max(0, reset_epoch - int(time.time()) + 1)
            time.sleep(min(sleep_for, 60))
            continue
        return resp
    return resp


def safe_get_json(url: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Any, int, Optional[str]]:
    """Safely get JSON from URL with error handling."""
    resp = _req("GET", url, params=params or {})
    try:
        resp.raise_for_status()
        return resp.json(), resp.status_code, None
    except requests.HTTPError as e:
        try:
            j = resp.json()
        except Exception:
            j = {"message": resp.text}
        msg = j.get("message") if isinstance(j, dict) else str(e)
        return None, resp.status_code, msg


def _flatten(prefix: str, obj: Any) -> List[Tuple[str, str]]:
    """Flatten nested dict/list into dot/bracket path keys to string values."""
    def _to_str(val: Any) -> str:
        if val is None or isinstance(val, (str, int, float, bool)):
            return str(val)
        return json.dumps(val, ensure_ascii=False)

    result = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            result.extend(_flatten(new_prefix, v))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_prefix = f"{prefix}[{i}]" if prefix else f"[{i}]"
            result.extend(_flatten(new_prefix, v))
    else:
        result.append((prefix, _to_str(obj)))
    
    return result


def query_huggingface_model(model_id: str) -> Dict[str, Any]:
    """Query HuggingFace for model information.
    
    Args:
        model_id: HuggingFace model ID
        
    Returns:
        Dictionary containing model information
    """
    try:
        api = HfApi()
        model_info = api.model_info(model_id, securityStatus=True)
        
        # Convert model info to dictionary format
        model_data = {
            'model_id': model_id,
            'status': 'success'
        }
        
        # Extract key information from model_info object
        for key, value in model_info.__dict__.items():
            if key in ['id', 'sha', 'lastModified', 'tags', 'downloads', 'likes', 'library_name', 'pipeline_tag']:
                model_data[key] = value
        
        return model_data
        
    except Exception as e:
        return {
            'model_id': model_id,
            'status': 'error',
            'error_message': str(e)
        }


def query_github_repo(owner: str, repo: str) -> Dict[str, Any]:
    """Query GitHub for repository information.
    
    Args:
        owner: GitHub owner/organization name
        repo: Repository name
        
    Returns:
        Dictionary containing repository information
    """
    try:
        # Repository core information
        repo_url = f"{API_ROOT}/repos/{owner}/{repo}"
        repo_json, code, err = safe_get_json(repo_url)
        
        if not repo_json:
            return {
                'owner': owner,
                'repo': repo,
                'status': 'error',
                'error_message': f"Failed to fetch repo: {code} {err}"
            }
        
        # Initialize result with basic info
        repo_data = {
            'owner': owner,
            'repo': repo,
            'status': 'success'
        }
        
        # Extract key repository information
        key_fields = [
            'id', 'name', 'full_name', 'description', 'html_url', 'clone_url',
            'created_at', 'updated_at', 'pushed_at', 'size', 'stargazers_count',
            'watchers_count', 'forks_count', 'open_issues_count', 'language',
            'has_issues', 'has_projects', 'has_downloads', 'has_wiki',
            'has_pages', 'archived', 'disabled', 'private', 'fork',
            'default_branch', 'topics'
        ]
        
        for field in key_fields:
            if field in repo_json:
                repo_data[f'repo_{field}'] = repo_json[field]
        
        # Get owner information
        owner_info = repo_json.get('owner', {})
        if owner_info:
            for key in ['login', 'id', 'type', 'html_url']:
                if key in owner_info:
                    repo_data[f'owner_{key}'] = owner_info[key]
        
        # Get additional repository data (non-fatal)
        topics_url = f"{API_ROOT}/repos/{owner}/{repo}/topics"
        topics_json, _, _ = safe_get_json(topics_url)
        if isinstance(topics_json, dict):
            repo_data['topics'] = ', '.join(topics_json.get("names", []))
        
        langs_url = f"{API_ROOT}/repos/{owner}/{repo}/languages"
        langs_json, _, _ = safe_get_json(langs_url)
        if isinstance(langs_json, dict):
            repo_data['languages'] = ', '.join(sorted(langs_json.keys()))
        
        return repo_data
        
    except Exception as e:
        return {
            'owner': owner,
            'repo': repo,
            'status': 'error',
            'error_message': str(e)
        }


def query_all_models(model_mappings: List[Tuple[str, str]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Query both HuggingFace and GitHub for all models in the mapping.
    
    Args:
        model_mappings: List of (huggingface_id, github_id) tuples
        
    Returns:
        Tuple of (huggingface_results, github_results)
    """
    huggingface_results = []
    github_results = []
    
    print(f"Querying {len(model_mappings)} models...")
    
    for i, (hf_id, gh_id) in enumerate(model_mappings, 1):
        print(f"Processing {i}/{len(model_mappings)}: {hf_id} -> {gh_id}")
        
        # Query HuggingFace
        print(f"  Querying HuggingFace: {hf_id}")
        hf_result = query_huggingface_model(hf_id)
        huggingface_results.append(hf_result)
        
        # Parse GitHub owner/repo from the ID
        if '/' in gh_id:
            owner, repo = gh_id.split('/', 1)
            print(f"  Querying GitHub: {owner}/{repo}")
            gh_result = query_github_repo(owner, repo)
            github_results.append(gh_result)
        else:
            print(f"  Warning: Invalid GitHub ID format: {gh_id}")
            github_results.append({
                'owner': 'unknown',
                'repo': 'unknown',
                'status': 'error',
                'error_message': f"Invalid GitHub ID format: {gh_id}"
            })
        
        # Add a small delay to be respectful to APIs
        time.sleep(0.5)
    
    return huggingface_results, github_results


def export_to_excel(hf_results: List[Dict[str, Any]], gh_results: List[Dict[str, Any]], output_file: str):
    """Export results to Excel file with separate tabs.
    
    Args:
        hf_results: HuggingFace query results
        gh_results: GitHub query results
        output_file: Output Excel file path
    """
    print(f"Exporting results to {output_file}...")
    
    # Convert to DataFrames
    hf_df = pd.DataFrame(hf_results)
    gh_df = pd.DataFrame(gh_results)
    
    # Handle datetime columns that might have timezone info
    for df in [hf_df, gh_df]:
        for col in df.columns:
            # Convert all values to strings to avoid datetime timezone issues
            df[col] = df[col].astype(str)
    
    # Write to Excel with separate sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        hf_df.to_excel(writer, sheet_name='HuggingFace', index=False)
        gh_df.to_excel(writer, sheet_name='GitHub', index=False)
    
    print(f"Successfully exported {len(hf_results)} HuggingFace results and {len(gh_results)} GitHub results to {output_file}")


def main():
    """Main function to orchestrate the querying process."""
    print("Model Scoring Query Tool")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv("HF_TOKEN"):
        print("Warning: No HF_TOKEN found in environment variables")
        print("Some HuggingFace operations may be limited")
    
    if not os.getenv("GITHUB_TOKEN"):
        print("Warning: No GITHUB_TOKEN found in environment variables")
        print("GitHub API rate limits may be more restrictive")
    
    # Parse model mappings
    mapping_file = "model_list_map.txt"
    if not os.path.exists(mapping_file):
        print(f"Error: {mapping_file} not found!")
        sys.exit(1)
    
    model_mappings = parse_model_mapping(mapping_file)
    if not model_mappings:
        print(f"Error: No valid model mappings found in {mapping_file}")
        sys.exit(1)
    
    print(f"Found {len(model_mappings)} model mappings")
    
    # Query all models
    hf_results, gh_results = query_all_models(model_mappings)
    
    # Export to Excel
    output_file = "combined_query.xlsx"
    export_to_excel(hf_results, gh_results, output_file)
    
    # Print summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"HuggingFace queries: {len(hf_results)} total")
    print(f"  - Successful: {sum(1 for r in hf_results if r.get('status') == 'success')}")
    print(f"  - Failed: {sum(1 for r in hf_results if r.get('status') == 'error')}")
    print(f"GitHub queries: {len(gh_results)} total")
    print(f"  - Successful: {sum(1 for r in gh_results if r.get('status') == 'success')}")
    print(f"  - Failed: {sum(1 for r in gh_results if r.get('status') == 'error')}")
    print(f"Results exported to: {output_file}")


if __name__ == "__main__":
    main()
