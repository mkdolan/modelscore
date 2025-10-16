#!/usr/bin/env python3
"""
Configuration management for the ModelScore application.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration settings."""
    
    # File paths
    model_list_file: str = "model_list_map.txt"
    output_dir: str = "../model_scores"
    
    # API settings
    github_token: Optional[str] = None
    
    def __post_init__(self):
        """Initialize derived paths and settings."""
        self.src_dir = Path(__file__).parent
        self.model_list_path = self.src_dir / self.model_list_file
        self.output_path = self.src_dir / self.output_dir
        
        # Ensure output directory exists
        self.output_path.mkdir(exist_ok=True)
    
    def get_model_csv_path(self, owner_name: str) -> Path:
        """Get the CSV path for a model owner."""
        return self.output_path / f"{owner_name}_model_info.csv"
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables."""
        import os
        return cls(
            github_token=os.getenv("GITHUB_TOKEN")
        )
