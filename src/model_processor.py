#!/usr/bin/env python3
"""
Model processing logic for the ModelScore application.
"""

import logging
import requests
from pathlib import Path
from typing import Tuple, Optional
from hf_model_query import get_model_info, export_model_info_to_csv
from hf_user_query import query_user_overview, append_user_info_to_csv
from hf_org_query import get_all_org_info, append_org_info_to_csv
from gh_sec2 import query_github_security
from config import Config


class ModelProcessor:
    """Handles processing of individual models."""
    
    def __init__(self, config: Config):
        """Initialize the model processor with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def _is_organization(self, owner_name: str) -> bool:
        """Check if an owner name is an organization or user.
        
        Args:
            owner_name: The HuggingFace owner name to check
            
        Returns:
            bool: True if it's an organization, False if it's a user
        """
        try:
            # Try user endpoint first
            user_url = f"https://huggingface.co/api/users/{owner_name}/overview"
            user_response = requests.get(user_url)
            
            if user_response.status_code == 200:
                return False  # It's a user
            elif user_response.status_code == 404:
                # Try organization endpoint
                org_url = f"https://huggingface.co/api/organizations/{owner_name}/overview"
                org_response = requests.get(org_url)
                
                if org_response.status_code == 200:
                    return True  # It's an organization
                else:
                    self.logger.warning(f"Could not determine if {owner_name} is user or organization")
                    return False  # Default to user
            else:
                self.logger.warning(f"Unexpected status code {user_response.status_code} for user {owner_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking owner type for {owner_name}: {e}")
            return False  # Default to user
    
    def process_model(self, hf_model_name: str, github_repo: str) -> bool:
        """Process a single model by querying HuggingFace and GitHub APIs.
        
        Args:
            hf_model_name: HuggingFace model name for HF API queries
            github_repo: GitHub repository name for GitHub API queries
            
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        self.logger.info(f"Processing model: {hf_model_name} (GitHub: {github_repo})")
        
        try:
            # Process HuggingFace model information
            if not self._process_huggingface_model(hf_model_name):
                return False
            
            # Process GitHub security information
            if not self._process_github_security(github_repo):
                self.logger.warning(f"GitHub security processing failed for {github_repo}")
                # Don't return False here as HF processing succeeded
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing model {hf_model_name}: {e}")
            return False
    
    def _process_huggingface_model(self, hf_model_name: str) -> bool:
        """Process HuggingFace model information.
        
        Args:
            hf_model_name: HuggingFace model name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get model information
            info = get_model_info(hf_model_name)
            self.logger.info(f"Retrieved model info: {info.modelId}, SHA: {info.sha}")
            
            # Extract owner and export model info
            owner_name = hf_model_name.split('/')[0]
            csv_path = self.config.get_model_csv_path(owner_name)
            export_model_info_to_csv(info, str(csv_path))
            self.logger.info(f"Model information exported to {csv_path}")
            
            # Get and append owner information (user or organization)
            if self._is_organization(owner_name):
                self.logger.info(f"Detected {owner_name} as organization")
                owner_info = get_all_org_info(owner_name)
                if owner_info:
                    append_org_info_to_csv(owner_info, str(csv_path))
                    self.logger.info("Organization information appended to CSV")
                else:
                    self.logger.warning("Failed to retrieve HuggingFace organization information")
            else:
                self.logger.info(f"Detected {owner_name} as user")
                user_info = query_user_overview(owner_name)
                if user_info:
                    append_user_info_to_csv(user_info, str(csv_path))
                    self.logger.info("User information appended to CSV")
                else:
                    self.logger.warning("Failed to retrieve HuggingFace user information")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing HuggingFace model {hf_model_name}: {e}")
            return False
    
    def _process_github_security(self, github_repo: str) -> bool:
        """Process GitHub security information.
        
        Args:
            github_repo: GitHub repository name in format "owner/repo"
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if '/' not in github_repo:
                self.logger.error(f"Invalid GitHub repository format: {github_repo}")
                return False
            
            owner, repo = github_repo.split('/', 1)
            security_csv_path = query_github_security(owner, repo)
            self.logger.info(f"GitHub security information exported to {security_csv_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error querying GitHub security for {github_repo}: {e}")
            return False
