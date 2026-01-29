from pathlib import Path
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

def scan_key_pairs(
    output_dir: Path,
    profile: str = None,
    region: str = "us-east-1",
    key_name: str = None
):
    boto_session = get_boto_session(profile, region)
    ec2_client = boto_session.client("ec2")

    filters = []
    if key_name:
        filters.append({'Name': 'key-name', 'Values': [key_name]})
        
    key_pairs = ec2_client.describe_key_pairs(Filters=filters)["KeyPairs"]
    
    # Add sanitized names
    for kp in key_pairs:
        kp['name_sanitized'] = kp['KeyName'].replace('-', '_').replace('.', '_').lower()
    
    output_file = output_dir / "key_pairs.tf"
    generate_tf(key_pairs, "aws_key_pair", output_file)
    print(f"Generated Terraform for {len(key_pairs)} Key Pairs -> {output_file}")
    # NOTE: Key pairs use data sources (not resources) because AWS doesn't expose
    # public key material for existing keys. They cannot be imported, only referenced.

def list_key_pairs(output_dir: Path):
    ImportManager(output_dir, "key_pairs").list_all()

def import_key_pair(key_name: str, output_dir: Path):
    ImportManager(output_dir, "key_pairs").find_and_import(key_name)
