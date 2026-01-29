from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_kms_aliases(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for KMS aliases (customer-created only) and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    kms_client = boto_session.client("kms")

    print(f"Scanning for KMS Aliases in region {region}...")

    # List all aliases with pagination
    aliases = []
    paginator = kms_client.get_paginator('list_aliases')

    for page in paginator.paginate():
        aliases.extend(page['Aliases'])

    if not aliases:
        print("No KMS aliases found")
        return

    print(f"Found {len(aliases)} KMS aliases (including AWS-managed)")

    # Filter out AWS-managed aliases (start with 'alias/aws/')
    customer_aliases = []
    for alias in aliases:
        alias_name = alias.get('AliasName', '')

        # Skip AWS-managed aliases
        if alias_name.startswith('alias/aws/'):
            continue

        # Skip aliases without a target key
        if 'TargetKeyId' not in alias:
            continue

        customer_aliases.append(alias)

    # Process resources to ensure proper naming
    customer_aliases = process_resources(customer_aliases, 'aliases')

    # Generate Terraform files
    output_file = output_dir / "kms_alias.tf"
    generate_tf(customer_aliases, "aws_kms_alias", output_file)
    print(f"Generated Terraform for {len(customer_aliases)} customer-created KMS Aliases -> {output_file}")

    # Generate import file
    generate_imports_file(
        "kms_alias",
        customer_aliases,
        remote_resource_id_key="AliasName",
        output_dir=output_dir,
        provider="aws"
    )


def list_kms_aliases(output_dir: Path):
    """Lists all KMS Alias resources previously generated."""
    ImportManager(output_dir, "kms_alias").list_all()


def import_kms_alias(alias_name: str, output_dir: Path):
    """Runs terraform import for a specific KMS Alias by its name."""
    ImportManager(output_dir, "kms_alias").find_and_import(alias_name)
