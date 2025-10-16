#!/usr/bin/env python3
"""
Model query utilities for interacting with Hugging Face Hub.
"""

from typing import Optional, Dict, Any
from huggingface_hub import HfApi
from excel_manager import ExcelManager


def get_model_info(model_name: str):
    """Fetch model information from Hugging Face Hub.

    Args:
        model_name: Full repository id of the model (e.g., "google-bert/bert-base-uncased").

    Returns:
        The result of HfApi.model_info(model_name).
    """
    api = HfApi()
    return api.model_info(model_name, securityStatus=True)


def export_model_info_to_excel(model_info, excel_manager: ExcelManager, model_name: str) -> None:
    """Export a model_info object to an Excel tab as key-value pairs.

    Args:
        model_info: The object returned by get_model_info.
        excel_manager: ExcelManager instance to write to.
        model_name: Model name for the tab name.
    """
    # Convert model info to dictionary format
    model_data = {}
    for key, value in model_info.__dict__.items():
        model_data[key] = value
    
    # Create tab name
    tab_name = f"{model_name}_model_info"
    
    # Use Excel manager to create the tab
    excel_manager.create_tab_from_key_value_pairs(tab_name, model_data)


def export_model_info_to_csv(model_info, csv_path: str = "../model_scores/{model_name}model_info.csv") -> None:
    """Export a model_info object to a CSV file as key-value pairs.
    
    DEPRECATED: Use export_model_info_to_excel instead.

    Args:
        model_info: The object returned by get_model_info.
        csv_path: Destination CSV path.
    """
    import csv
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Key', 'Value'])
        for key, value in model_info.__dict__.items():
            writer.writerow([key, value])


def query_and_export_model(model_name: str, excel_manager: ExcelManager) -> None:
    """Convenience function to fetch model info and export it to Excel.

    Args:
        model_name: Full repository id of the model.
        excel_manager: ExcelManager instance to write to.
    """
    info = get_model_info(model_name)
    export_model_info_to_excel(info, excel_manager, model_name)


