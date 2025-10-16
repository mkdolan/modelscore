# ModelScore2

ModelScore2 is a comprehensive tool for analyzing and scoring machine learning models by gathering data from both HuggingFace and GitHub APIs. The application collects detailed information about models, their creators (users or organizations), and associated GitHub repositories to provide insights into model quality, security, and development practices.

### Usage

```bash
# Set GitHub token for enhanced API access
export GITHUB_TOKEN=your_github_token

# Run the analysis
python main.py
```

The application will process all models defined in `model_list_map.txt` and generate a comprehensive Excel report in the `model_scores/` directory.

## How it Works

### Model Definition (`model_list_map.txt`)
Models to be analyzed are defined in `model_list_map.txt` using a simple CSV format:
```
# format: HuggingFace Name, GitHub org/repo
meta-llama/Llama-4-Scout-17B-16E-Instruct, meta-llama/llama-models
ibm-granite/granite-4.0-micro, ibm-granite/granite-4.0-language-models
suno/bark, suno-ai/bark
```

Each line maps a HuggingFace model to its corresponding GitHub repository for comprehensive analysis.

### Core Components

#### `main.py` - Application Entry Point
- Reads the model list from `model_list_map.txt`
- Orchestrates the processing workflow for each model
- Manages logging and error handling
- Generates a timestamped Excel report with all collected data

#### `model_processor.py` - Model Processing Logic
- Handles the complete workflow for analyzing each model
- Determines whether a model owner is a user or organization
- Coordinates data collection from HuggingFace and GitHub APIs
- Manages error handling and logging for individual model processing

### Query Modules

#### `hf_model_query.py` - HuggingFace Model Information
- Fetches detailed model metadata from HuggingFace Hub API
- Retrieves model information including SHA, tags, downloads, and security status
- Exports model data to Excel tabs in key-value format

#### `hf_user_query.py` - HuggingFace User Information  
- Queries HuggingFace API for individual user profiles
- Collects user overview data including bio, location, and activity metrics
- Appends user information to Excel when model owner is an individual user

#### `hf_org_query.py` - HuggingFace Organization Information
- Fetches comprehensive organization data from HuggingFace API
- Collects organization overview, members, models, datasets, and spaces
- Provides detailed metrics about organization size and activity
- Appends organization information to Excel when model owner is an organization

#### `gh_repo_query.py` - GitHub Repository Security Analysis
- Performs security evaluation of GitHub repositories
- Collects repository metadata, owner information, and security settings
- Checks for 2FA enforcement, member security practices, and repository settings
- Exports comprehensive security checklist data to Excel

#### `excel_manager.py` - Excel Output Management
- Manages multi-tab Excel file creation with timestamped filenames
- Handles tab naming, data formatting, and file organization
- Ensures proper Excel formatting and data structure across all tabs

## Output Structure

The application generates a timestamped Excel file with organized tabs:
- `{N}-HF-model`: HuggingFace model information
- `{N}-HF-user`: User information (if model owner is individual)
- `{N}-HF-org`: Organization information (if model owner is organization)  
- `{N}-GH-repo`: GitHub repository security analysis

Where `{N}` corresponds to the row number from the model list file.



