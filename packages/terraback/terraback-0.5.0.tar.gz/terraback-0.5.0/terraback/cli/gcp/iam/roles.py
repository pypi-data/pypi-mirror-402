from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from google.cloud import iam_admin_v1
from google.api_core.exceptions import GoogleAPIError


def _process_role_data(role: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP IAM role data for Terraform generation."""
    role_data = {
        'name': role.name.split('/')[-1],
        'role_id': role.name.split('/')[-1],
        'title': role.title,
        'description': role.description,
        'stage': role.stage.name if hasattr(role, 'stage') else 'GA',
        'deleted': role.deleted if hasattr(role, 'deleted') else False,
        'project': project_id,
        'permissions': list(role.included_permissions) if hasattr(role, 'included_permissions') else []
    }
    
    # Extract etag if available
    if hasattr(role, 'etag'):
        role_data['etag'] = role.etag
    
    return role_data


def get_role_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch IAM Role data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of role data dictionaries
    """
    credentials, default_project = get_gcp_credentials()
    project_id = project_id or default_project
    
    client = iam_admin_v1.IAMClient(credentials=credentials)
    roles_data = []
    
    try:
        # List custom roles for the project
        parent = f"projects/{project_id}"
        request = iam_admin_v1.ListRolesRequest(parent=parent)
        
        for role in client.list_roles(request=request):
            if not role.deleted:  # Skip deleted roles
                role_data = _process_role_data(role, project_id)
                roles_data.append(role_data)
                
    except GoogleAPIError as e:
        print(f"Error fetching GCP IAM roles: {e}")
        
    return roles_data


def scan_iam_roles(output_dir: Path, project_id: Optional[str] = None):
    """
    Scan GCP IAM roles and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
    """
    roles = get_role_data(project_id)
    
    if not roles:
        print("No IAM roles found.")
        return
        
    output_file = output_dir / "gcp_iam_roles.tf"
    generate_tf(roles, "gcp_iam_roles", output_file)
    print(f"Generated Terraform for {len(roles)} GCP IAM Roles -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_iam_roles", 
        roles, 
        remote_resource_id_key="name",
        output_dir=output_dir, provider="gcp"
    )


def list_iam_roles(output_dir: Path):
    """List all imported GCP IAM roles."""
    ImportManager(output_dir, "gcp_iam_roles").list_all()


def import_iam_role(role_name: str, output_dir: Path):
    """Import a specific GCP IAM role."""
    ImportManager(output_dir, "gcp_iam_roles").find_and_import(role_name)