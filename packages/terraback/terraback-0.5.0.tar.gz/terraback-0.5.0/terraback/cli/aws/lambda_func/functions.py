from pathlib import Path
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from .layers import scan_lambda_layers
from typing import Set, Tuple
from terraback.cli.aws.resource_processor import process_resources

# --- Helper functions to handle pagination and denest the logic ---

def _get_all_function_names(lambda_client):
    """A generator function that yields each Lambda function's name, handling pagination."""
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate():
        for func in page.get('Functions', []):
            yield func['FunctionName']

def _get_function_details(lambda_client, function_names):
    """A generator that fetches full details for each function name, handling exceptions."""
    for name in function_names:
        try:
            details = lambda_client.get_function(FunctionName=name)
            config = details['Configuration']
            config['Tags'] = details.get('Tags', {})
            yield config
        except Exception as e:
            print(f"  - Could not retrieve details for function {name}: {e}")
            continue

# --- Main scan function ---

def scan_lambda_functions(output_dir: Path, profile: str = None, region: str = "us-east-1"):
    """
    Scans for AWS Lambda functions and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    lambda_client = boto_session.client("lambda")
    print(f"Scanning for Lambda Functions in region {region}...")


    # 1. Get all function names.
    all_function_names = _get_all_function_names(lambda_client)
    
    # 2. Get the full details for each function.
    all_functions = list(_get_function_details(lambda_client, all_function_names))
    
    # Process resources to ensure proper naming
    all_functions = process_resources(all_functions, 'functions')

    # Collect layers referenced by functions
    layers_in_use: Set[Tuple[str, int]] = set()
    for func in all_functions:
        for layer in func.get("Layers", []):
            arn = layer.get("Arn") or layer.get("LayerVersionArn")
            if not arn:
                continue
            parts = arn.split(":")
            if len(parts) < 2:
                continue
            layer_name = parts[-2]
            try:
                version = int(parts[-1])
            except ValueError:
                continue
            layers_in_use.add((layer_name, version))

    # 3. Generate the output files.
    output_file = output_dir / "lambda_function.tf"
    generate_tf(all_functions, "aws_lambda_function", output_file)
    print(f"Generated Terraform for {len(all_functions)} Lambda Functions -> {output_file}")
    generate_imports_file("lambda_function", all_functions, remote_resource_id_key="FunctionName", output_dir=output_dir, provider="aws")

    if layers_in_use:
        scan_lambda_layers(
            output_dir,
            profile,
            region,
            versions_in_use=layers_in_use,
        )


# --- CLI helper functions ---

def list_lambda_functions(output_dir: Path):
    """Lists all Lambda Function resources previously generated."""
    ImportManager(output_dir, "lambda_function").list_all()

def import_lambda_function(function_name: str, output_dir: Path):
    """Runs terraform import for a specific Lambda Function by its name."""
    ImportManager(output_dir, "lambda_function").find_and_import(function_name)
