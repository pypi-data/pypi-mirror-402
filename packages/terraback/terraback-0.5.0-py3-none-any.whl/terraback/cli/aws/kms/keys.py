from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources


def scan_kms_keys(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    """
    Scans for KMS keys (customer-managed only) and generates Terraform code.
    """
    boto_session = get_boto_session(profile, region)
    kms_client = boto_session.client("kms")

    print(f"Scanning for KMS Keys in region {region}...")

    # List all keys with pagination
    key_ids = []
    paginator = kms_client.get_paginator('list_keys')

    for page in paginator.paginate():
        key_ids.extend(page['Keys'])

    if not key_ids:
        print("No KMS keys found")
        return

    print(f"Found {len(key_ids)} KMS keys (including AWS-managed)")

    # Get detailed information for each key, filtering out AWS-managed keys
    detailed_keys = []
    for key_info in key_ids:
        key_id = key_info['KeyId']
        try:
            # Get key metadata
            response = kms_client.describe_key(KeyId=key_id)
            key = response['KeyMetadata']

            # Skip AWS-managed keys
            if key.get('KeyManager') == 'AWS':
                continue

            # Skip keys that are pending deletion
            if key.get('KeyState') == 'PendingDeletion':
                print(f"  - Skipping key {key_id}: pending deletion")
                continue

            # Get tags
            try:
                tags_response = kms_client.list_resource_tags(KeyId=key_id)
                if tags_response.get('Tags'):
                    key['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
            except Exception as e:
                print(f"  - Could not get tags for key {key_id}: {e}")

            # Get key rotation status
            try:
                rotation_response = kms_client.get_key_rotation_status(KeyId=key_id)
                key['KeyRotationEnabled'] = rotation_response.get('KeyRotationEnabled', False)
            except Exception as e:
                print(f"  - Could not get rotation status for key {key_id}: {e}")
                key['KeyRotationEnabled'] = False

            detailed_keys.append(key)

        except Exception as e:
            print(f"  - Could not retrieve details for key {key_id}: {e}")
            continue

    # Process resources to ensure proper naming
    detailed_keys = process_resources(detailed_keys, 'keys')

    # Generate Terraform files
    output_file = output_dir / "kms_key.tf"
    generate_tf(detailed_keys, "aws_kms_key", output_file)
    print(f"Generated Terraform for {len(detailed_keys)} customer-managed KMS Keys -> {output_file}")

    # Generate import file
    generate_imports_file(
        "aws_kms_key",
        detailed_keys,
        remote_resource_id_key="KeyId",
        output_dir=output_dir,
        provider="aws"
    )


def list_kms_keys(output_dir: Path):
    """Lists all KMS Key resources previously generated."""
    ImportManager(output_dir, "kms_key").list_all()


def import_kms_key(key_id: str, output_dir: Path):
    """Runs terraform import for a specific KMS Key by its ID."""
    ImportManager(output_dir, "kms_key").find_and_import(key_id)
