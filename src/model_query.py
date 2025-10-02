#!/usr/bin/env python3
"""
Model query utilities for interacting with Hugging Face Hub.
"""

from typing import Optional
from huggingface_hub import HfApi
import csv


def get_model_info(model_name: str):
    """Fetch model information from Hugging Face Hub.

    Args:
        model_name: Full repository id of the model (e.g., "google-bert/bert-base-uncased").

    Returns:
        The result of HfApi.model_info(model_name).
    """
    api = HfApi()
    return api.model_info(model_name, securityStatus=True)


def export_model_info_to_csv(model_info, csv_path: str = "model_info.csv") -> None:
    """Export a model_info object to a CSV file as key-value pairs.

    Args:
        model_info: The object returned by get_model_info.
        csv_path: Destination CSV path.
    """
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Key', 'Value'])
        for key, value in model_info.__dict__.items():
            writer.writerow([key, value])


def query_and_export_model(model_name: str, csv_path: str = "model_info.csv") -> None:
    """Convenience function to fetch model info and export it to CSV.

    Args:
        model_name: Full repository id of the model.
        csv_path: Destination CSV path for export.
    """
    info = get_model_info(model_name)
    export_model_info_to_csv(info, csv_path)


