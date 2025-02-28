# TabPFN Cloud Function - Developer Guide

## Commands
- Deploy: `./deploy.ps1` or `gcloud functions deploy infer-category --gen2 --region=[region] --runtime=python310 --source=. --entry-point=infer_category --trigger-http --memory=2048MB --timeout=540s --env-vars-file=.env.yaml`
- Local testing: `python -m functions_framework --target infer_category --debug`
- Type checking: `mypy *.py`
- Linting: `flake8 *.py`

## Code Style
- Follow PEP 8 for Python code
- Use type annotations for all function parameters and return types
- CamelCase for classes, snake_case for functions and variables
- Comprehensive docstrings for functions and classes
- Error handling with appropriate logging
- Keep imports organized: standard library, third-party, then local modules
- Environment variables for configuration, no hardcoded credentials
- JSON for API request/response bodies