from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_dynamodb_tables(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for DynamoDB tables and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    dynamodb_client = boto_session.client("dynamodb")

    print(f"Scanning for DynamoDB Tables in region {region}...")

    # List all tables with pagination
    table_names = []
    paginator = dynamodb_client.get_paginator('list_tables')

    for page in paginator.paginate():
        table_names.extend(page['TableNames'])

    if not table_names:
        print("No DynamoDB tables found")
        return

    print(f"Found {len(table_names)} DynamoDB tables")

    # Get detailed information for each table
    detailed_tables = []
    for table_name in table_names:
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response['Table']

            # Get tags
            try:
                tags_response = dynamodb_client.list_tags_of_resource(
                    ResourceArn=table['TableArn']
                )
                if tags_response.get('Tags'):
                    table['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
            except Exception as e:
                print(f"  - Could not get tags for table {table_name}: {e}")

            # Get Time to Live settings
            try:
                ttl_response = dynamodb_client.describe_time_to_live(TableName=table_name)
                if ttl_response.get('TimeToLiveDescription'):
                    table['TimeToLiveDescription'] = ttl_response['TimeToLiveDescription']
            except Exception as e:
                print(f"  - Could not get TTL for table {table_name}: {e}")

            # Get continuous backups
            try:
                backup_response = dynamodb_client.describe_continuous_backups(TableName=table_name)
                if backup_response.get('ContinuousBackupsDescription'):
                    table['ContinuousBackupsDescription'] = backup_response['ContinuousBackupsDescription']
            except Exception as e:
                print(f"  - Could not get backup info for table {table_name}: {e}")

            detailed_tables.append(table)

        except Exception as e:
            print(f"  - Could not retrieve details for table {table_name}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_tables = process_resources(detailed_tables, 'tables')

    # Generate Terraform files
    output_file = output_dir / "dynamodb_table.tf"
    generate_tf(detailed_tables, "aws_dynamodb_table", output_file)
    print(f"Generated Terraform for {len(detailed_tables)} DynamoDB Tables -> {output_file}")

    # Generate import file
    generate_imports_file(
        "aws_dynamodb_table",
        detailed_tables,
        remote_resource_id_key="TableName",
        output_dir=output_dir,
        provider="aws"
    )


def list_dynamodb_tables(output_dir: Path):
    """Lists all DynamoDB Table resources previously generated."""
    ImportManager(output_dir, "dynamodb_table").list_all()


def import_dynamodb_table(table_name: str, output_dir: Path):
    """Runs terraform import for a specific DynamoDB Table by its name."""
    ImportManager(output_dir, "dynamodb_table").find_and_import(table_name)
