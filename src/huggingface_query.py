#!/usr/bin/env python3
"""
Hugging Face Hub client library example for querying models
"""

from huggingface_hub import HfApi, HfFolder
import os

def query_huggingface_models():
    """Query Hugging Face models using the client library"""
    
    # Initialize the Hugging Face API client
    api = HfApi()
    
    try:
        # List some popular models
        print("Popular Models:")
        models = api.list_models(sort="downloads", direction=-1, limit=5)
        for model in models:
            print(f"- {model.id}: {model.downloads} downloads")
        
        print("\n" + "="*50 + "\n")
        
        # Search for specific models (e.g., text-generation models)
        print("Text Generation Models:")
        text_models = api.list_models(search="text-generation", limit=5)
        for model in text_models:
            print(f"- {model.id}: {model.tags}")
        
        print("\n" + "="*50 + "\n")
        
        # Get detailed information about a specific model
        print("Detailed Model Information:")
        model_info = api.model_info("gpt2")
        print(f"Model ID: {model_info.id}")
        print(f"Description: {model_info.description}")
        print(f"Tags: {model_info.tags}")
        print(f"Downloads: {model_info.downloads}")
        print(f"Likes: {model_info.likes}")
        
    except Exception as e:
        print(f"Error querying Hugging Face: {e}")

def query_model_inference(model_id="gpt2", prompt="Hello, how are you?"):
    """Query a model for inference (requires API token for private models)"""
    
    try:
        # For public models, we can use the inference API
        from huggingface_hub import InferenceApi
        
        # Initialize inference client
        inference = InferenceApi(model_id)
        
        # For demonstration, we'll show how to use it
        print(f"\nInference example for model: {model_id}")
        print("This would normally make an API call to get model predictions")
        print(f"Prompt: {prompt}")
        
    except Exception as e:
        print(f"Error in inference query: {e}")

def main():
    """Main function"""
    print("Hugging Face Hub Client Library Query Example")
    print("="*50)
    
    # Check if Hugging Face token is available
    token = os.getenv("HF_TOKEN")
    if not token:
        print("Warning: No HF_TOKEN found in environment variables")
        print("Some operations may be limited")
    
    # Query models
    query_huggingface_models()
    
    # Query inference (example)
    query_model_inference()

if __name__ == "__main__":
    main()