from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.terraform_generator.filters import to_terraform_resource_name
from google.cloud import iam_admin_v1
from google.api_core.exceptions import GoogleAPIError


def _process_service_account_data(sa: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP service account data for Terraform generation."""
    account_id = sa.email.split('@')[0]
    sa_data = {
        'account_id': account_id,
        'display_name': sa.display_name,
        'description': sa.description if hasattr(sa, 'description') else '',
        'email': sa.email,
        'name': sa.name,
        'unique_id': sa.unique_id,
        'disabled': sa.disabled if hasattr(sa, 'disabled') else False,
        'project': project_id,
        'name_sanitized': to_terraform_resource_name(account_id),
    }
    
    return sa_data


def get_service_account_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Service Account data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of service account data dictionaries
    """
    credentials, default_project = get_gcp_credentials()
    project_id = project_id or default_project
    
    client = iam_admin_v1.IAMClient(credentials=credentials)
    sa_data = []
    
    try:
        # List service accounts for the project
        project_name = f"projects/{project_id}"
        request = iam_admin_v1.ListServiceAccountsRequest(name=project_name)
        
        for sa in client.list_service_accounts(request=request):
            if not sa.disabled:  # Skip disabled service accounts by default
                sa_info = _process_service_account_data(sa, project_id)
                sa_data.append(sa_info)
                
    except GoogleAPIError as e:
        print(f"Error fetching GCP service accounts: {e}")
        
    return sa_data


def scan_service_accounts(output_dir: Path, project_id: Optional[str] = None):
    """
    Scan GCP service accounts and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
    """
    service_accounts = get_service_account_data(project_id)
    
    if not service_accounts:
        print("No service accounts found.")
        return
        
    output_file = output_dir / "gcp_service_accounts.tf"
    generate_tf(service_accounts, "gcp_service_accounts", output_file)
    print(f"Generated Terraform for {len(service_accounts)} GCP Service Accounts -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_service_accounts", 
        service_accounts, 
        remote_resource_id_key="email",
        output_dir=output_dir, provider="gcp"
    )


def list_service_accounts(output_dir: Path):
    """List all imported GCP service accounts."""
    ImportManager(output_dir, "gcp_service_accounts").list_all()


def import_service_account(email: str, output_dir: Path):
    """Import a specific GCP service account."""
    ImportManager(output_dir, "gcp_service_accounts").find_and_import(email)