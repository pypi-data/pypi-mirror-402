from pathlib import Path
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources

def scan_roles(output_dir: Path, profile: str = None, region: str = "us-east-1"):
    boto_session = get_boto_session(profile, region)
    iam_client = boto_session.client("iam")
    
    paginator = iam_client.get_paginator('list_roles')
    roles = []
    for page in paginator.paginate():
        for role in page['Roles']:
            # Fetch tags for each role
            try:
                tags_response = iam_client.list_role_tags(RoleName=role['RoleName'])
                if tags_response.get('Tags'):
                    role['Tags'] = {tag['Key']: tag['Value'] for tag in tags_response['Tags']}
            except Exception as e:
                print(f"Warning: Could not fetch tags for role {role['RoleName']}: {e}")
            roles.append(role)
    
    # Process resources to filter AWS-managed roles and ensure proper naming
    roles = process_resources(roles, 'roles')
        
    output_file = output_dir / "iam_roles.tf"
    generate_tf(roles, "aws_iam_roles", output_file)
    print(f"Generated Terraform for {len(roles)} IAM Roles -> {output_file}")
    generate_imports_file("iam_roles", roles, remote_resource_id_key="RoleName", output_dir=output_dir, provider="aws")

def list_roles(output_dir: Path):
    ImportManager(output_dir, "iam_roles").list_all()

def import_role(role_name: str, output_dir: Path):
    ImportManager(output_dir, "iam_roles").find_and_import(role_name)
