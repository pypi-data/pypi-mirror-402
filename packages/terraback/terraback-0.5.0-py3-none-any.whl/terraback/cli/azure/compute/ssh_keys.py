"""Azure SSH Public Keys scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="ssh-key", help="Scan and import Azure SSH Public Keys.")


def scan_ssh_keys(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure SSH Public Keys and generate Terraform configurations.
    
    This function retrieves all SSH public keys from the specified subscription
    or resource group and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of SSH key resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    compute_client = get_azure_client('ComputeManagementClient', subscription_id)
    ssh_keys: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure SSH Public Keys...")
    print("Scanning for SSH Public Keys...")
    
    # List SSH public keys with proper error handling
    @safe_azure_operation("list SSH keys", default_return=[])
    def list_keys():
        if resource_group_name:
            return list(compute_client.ssh_public_keys.list_by_resource_group(resource_group_name))
        else:
            return list(compute_client.ssh_public_keys.list_by_subscription())
    
    ssh_key_list = list_keys()
    
    # Process each SSH key
    for ssh_key in ssh_key_list:
        ssh_key_data = format_resource_dict(ssh_key, 'ssh_public_key')
        ssh_keys.append(ssh_key_data)
        logger.debug(f"Processed SSH key: {ssh_key.name}")    # Process resources before generation
    ssh_keys = process_resources(ssh_keys, "azure_ssh_public_key")
    

    
    # Generate Terraform files if resources found
    if ssh_keys:
        generate_tf_auto(ssh_keys, "azure_ssh_public_key", output_dir)
        
        generate_imports_file(
            "azure_ssh_public_key",
            ssh_keys,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No SSH Keys found.")
        logger.info("No SSH Keys found.")
    
    return ssh_keys


@app.command("scan")
def scan_ssh_keys_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure SSH Public Keys and generates Terraform code."""
    typer.echo(f"Scanning for Azure SSH Keys in subscription '{subscription_id}'...")
    
    try:
        scan_ssh_keys(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning SSH Keys: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_ssh_keys(
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Lists all SSH Key resources previously generated."""
    ImportManager(output_dir, "azure_ssh_public_key").list_all()


@app.command("import")
def import_ssh_key(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the SSH Key to import."),
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Runs terraform import for a specific SSH Key."""
    ImportManager(output_dir, "azure_ssh_public_key").find_and_import(resource_id)