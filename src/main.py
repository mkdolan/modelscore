#!/usr/bin/env python3
"""
Main entry point for the ModelScore application.
"""

import logging
from pathlib import Path
from typing import List, Tuple
from config import Config
from model_processor import ModelProcessor


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def read_model_list(config: Config) -> List[Tuple[str, str]]:
    """Read and parse the model list from the configured file.
    
    Args:
        config: Application configuration
        
    Returns:
        List of tuples containing (hf_model_name, github_repo_name)
    """
    models = []
    
    try:
        with open(config.model_list_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse the line: HuggingFace Name, GitHub org/repo
                parts = line.split(',')
                if len(parts) != 2:
                    logging.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                
                hf_name = parts[0].strip()
                github_repo = parts[1].strip()
                models.append((hf_name, github_repo))
                
    except FileNotFoundError:
        logging.error(f"Model list file not found: {config.model_list_path}")
        return []
    except Exception as e:
        logging.error(f"Error reading model list file: {e}")
        return []
    
    return models


def main():
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config.from_env()
    logger.info("Application started")
    
    # Read model list
    models = read_model_list(config)
    if not models:
        logger.error("No models found in model list file")
        return
    
    logger.info(f"Found {len(models)} models to process")
    
    # Initialize model processor
    processor = ModelProcessor(config)
    
    # Process each model
    successful = 0
    failed = 0
    
    for i, (hf_model_name, github_repo) in enumerate(models, 1):
        logger.info(f"Processing model {i}/{len(models)}")
        
        if processor.process_model(hf_model_name, github_repo):
            successful += 1
        else:
            failed += 1
    
    # Save Excel file
    excel_manager = config.get_excel_manager()
    excel_path = excel_manager.save()
    logger.info(f"Excel file saved: {excel_path}")
    
    # Summary
    logger.info(f"Processing complete: {successful} successful, {failed} failed")


if __name__ == "__main__":
    main()