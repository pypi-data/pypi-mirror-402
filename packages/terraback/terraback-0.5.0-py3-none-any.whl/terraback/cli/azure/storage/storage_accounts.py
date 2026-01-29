import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import AzureError

from terraback.cli.azure.session import get_cached_azure_session, get_default_subscription_id
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.resource_processor import process_resources
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.utils.cross_scan_registry import cross_scan_registry
import logging

logger = logging.getLogger(__name__)

app = typer.Typer(name="account", help="Scan and import Azure Storage Accounts.")

def get_storage_account_data(subscription_id: str = None, resource_group_name: Optional[str] = None, location: Optional[str] = None, generate_files: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch Storage Account data from Azure.
    
    Args:
        subscription_id: Azure subscription ID (optional)
        resource_group_name: Optional resource group filter
        location: Optional location filter
    
    Returns:
        List of storage account data dictionaries
    """
    session = get_cached_azure_session(subscription_id)
    storage_client = StorageManagementClient(**session)
    
    storage_accounts = []
    
    try:
        # Get storage accounts either from specific resource group or all
        if resource_group_name:
            account_list = storage_client.storage_accounts.list_by_resource_group(resource_group_name)
        else:
            account_list = storage_client.storage_accounts.list()
        
        for account in account_list:
            # Apply location filter if specified
            if location and account.location != location:
                continue
                
            # Parse resource group from ID
            rg_name = account.id.split('/')[4]
            
            # Get detailed properties with error handling
            @safe_azure_operation(f"get storage account details for {account.name}", default_return=account)
            def get_account_details():
                return storage_client.storage_accounts.get_properties(
                    resource_group_name=rg_name,
                    account_name=account.name
                )
            
            account_details = get_account_details()
            
            # Use the common format_resource_dict function
            account_data = format_resource_dict(account_details, 'storage_account')
            
            # Add basic fields that might not be in format_resource_dict
            account_data.update({
                "name": account.name,
                "id": account.id,
                "resource_group_name": rg_name,
                "location": account.location,
            })
            
            # Format network rules
            _format_network_rules(account_data, account_details)
            
            # Format identity information
            _format_identity(account_data, account_details)
            
            # Format blob properties
            _format_blob_properties(account_data, account_details)
            
            # Format static website
            _format_static_website(account_data, account_details)
            
            # Format encryption settings
            _format_encryption_settings(account_data, account_details)
            
            # Format all template attributes
            _format_template_attributes(account_data, account, account_details)
            
            storage_accounts.append(account_data)
            
            # Register in cross-scan registry for cross-resource references
            cross_scan_registry.register(
                resource_type="azure_storage_account",
                item_id=account.id,
                data=account_data
            )
            
    except AzureError as e:
        typer.echo(f"Error fetching storage accounts: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return storage_accounts


def _format_network_rules(account_data: Dict[str, Any], account_details: Any) -> None:
    """Format network rules for the storage account."""
    if not hasattr(account_details, 'network_rule_set') or not account_details.network_rule_set:
        return
        
    network_rules = account_details.network_rule_set
    
    # Handle bypass - it might be a string or list
    bypass_list = []
    if network_rules.bypass:
        if isinstance(network_rules.bypass, str):
            bypass_list = [network_rules.bypass]
        elif hasattr(network_rules.bypass, '__iter__'):
            # If it's an iterable but not a string, convert properly
            bypass_list = [str(item) for item in network_rules.bypass]
    else:
        bypass_list = ["AzureServices"]
    
    account_data["network_rules_formatted"] = {
        "default_action": network_rules.default_action if network_rules.default_action else "Allow",
        "bypass": bypass_list,
        "ip_rules": [rule.ip_address_or_range for rule in network_rules.ip_rules] if network_rules.ip_rules else [],
        "virtual_network_subnet_ids": [rule.virtual_network_resource_id for rule in network_rules.virtual_network_rules] if network_rules.virtual_network_rules else [],
    }
    
    # Check if public network access is disabled
    if network_rules.default_action and network_rules.default_action == "Deny":
        account_data["public_network_access_enabled"] = False


def _format_identity(account_data: Dict[str, Any], account_details: Any) -> None:
    """Format identity information for the storage account."""
    if not hasattr(account_details, 'identity') or not account_details.identity:
        return
        
    account_data["identity_formatted"] = {
        "type": account_details.identity.type if account_details.identity.type else "None",
        "principal_id": account_details.identity.principal_id,
        "tenant_id": account_details.identity.tenant_id,
    }
    
    if hasattr(account_details.identity, 'user_assigned_identities') and account_details.identity.user_assigned_identities:
        account_data["identity_formatted"]["identity_ids"] = list(account_details.identity.user_assigned_identities.keys())


def _format_blob_properties(account_data: Dict[str, Any], account_details: Any) -> None:
    """Format blob properties for the storage account."""
    if not hasattr(account_details, 'blob_properties') or not account_details.blob_properties:
        return
        
    blob_props = account_details.blob_properties
    account_data["blob_properties_formatted"] = {
        "versioning_enabled": blob_props.is_versioning_enabled if hasattr(blob_props, 'is_versioning_enabled') else False,
        "change_feed_enabled": blob_props.change_feed.enabled if hasattr(blob_props, 'change_feed') and blob_props.change_feed else False,
        "last_access_time_enabled": blob_props.last_access_time_tracking_policy.enable if hasattr(blob_props, 'last_access_time_tracking_policy') and blob_props.last_access_time_tracking_policy else False,
        "delete_retention_policy": {
            "days": blob_props.delete_retention_policy.days if hasattr(blob_props, 'delete_retention_policy') and blob_props.delete_retention_policy and blob_props.delete_retention_policy.enabled else 0
        },
        "container_delete_retention_policy": {
            "days": blob_props.container_delete_retention_policy.days if hasattr(blob_props, 'container_delete_retention_policy') and blob_props.container_delete_retention_policy and blob_props.container_delete_retention_policy.enabled else 0
        }
    }


def _format_static_website(account_data: Dict[str, Any], account_details: Any) -> None:
    """Format static website settings for the storage account."""
    if hasattr(account_details, 'static_website') and account_details.static_website and account_details.static_website.enabled:
        account_data["static_website_formatted"] = {
            "index_document": account_details.static_website.index_document,
            "error_404_document": account_details.static_website.error_404_document,
        }


def _format_encryption_settings(account_data: Dict[str, Any], account_details: Any) -> None:
    """Format encryption settings for the storage account."""
    if hasattr(account_details, 'encryption') and account_details.encryption:
        if hasattr(account_details.encryption, 'require_infrastructure_encryption'):
            account_data["infrastructure_encryption_enabled"] = account_details.encryption.require_infrastructure_encryption
        
        # Format key vault encryption if present
        if hasattr(account_details.encryption, 'key_vault_properties') and account_details.encryption.key_vault_properties:
            account_data["customer_managed_key"] = {
                "key_vault_key_id": account_details.encryption.key_vault_properties.key_name,
                "user_assigned_identity_id": getattr(account_details.encryption.key_vault_properties, 'user_assigned_identity_id', None)
            }


def _format_template_attributes(account_data: Dict[str, Any], account: Any, account_details: Any) -> None:
    """Format all storage account attributes to match Jinja2 template expectations."""
    
    # Map basic account settings with proper defaults
    if hasattr(account, 'sku'):
        account_data['account_tier'] = account.sku.tier if account.sku and account.sku.tier else "Standard"
        account_data['account_replication_type'] = account.sku.name.split('_')[1] if account.sku else "LRS"
    
    if hasattr(account, 'kind'):
        account_data['account_kind'] = account.kind if account.kind else "StorageV2"
    
    # Map access tier
    if hasattr(account_details, 'access_tier'):
        account_data['access_tier'] = getattr(account_details, 'access_tier', 'Hot')
    
    # Security settings - convert Azure API names to Terraform attribute names
    if hasattr(account_details, 'enable_https_traffic_only'):
        account_data['https_traffic_only_enabled'] = getattr(account_details, 'enable_https_traffic_only', True)
    
    if hasattr(account_details, 'minimum_tls_version'):
        account_data['min_tls_version'] = getattr(account_details, 'minimum_tls_version', 'TLS1_2')
    
    # Convert blob public access setting
    if hasattr(account_details, 'allow_blob_public_access'):
        account_data['allow_nested_items_to_be_public'] = getattr(account_details, 'allow_blob_public_access', False)
    
    if hasattr(account_details, 'allow_shared_key_access'):
        account_data['shared_access_key_enabled'] = getattr(account_details, 'allow_shared_key_access', True)
    
    # Set default for public network access
    if 'public_network_access_enabled' not in account_data:
        account_data['public_network_access_enabled'] = True
    
    # Handle tags - ensure empty tags are handled properly
    if not hasattr(account, 'tags') or not account.tags:
        account_data['tags'] = {}
    else:
        account_data['tags'] = dict(account.tags) if account.tags else {}
    
    # Set default values for optional properties if not present
    if 'infrastructure_encryption_enabled' not in account_data:
        account_data['infrastructure_encryption_enabled'] = False
    
    # Set sanitized name for resource naming
    account_data['name_sanitized'] = account.name.replace('-', '_').lower()
    
    # Map formatted attributes to template-expected names
    if 'network_rules_formatted' in account_data:
        account_data['network_rules'] = account_data['network_rules_formatted']
    
    if 'identity_formatted' in account_data:
        account_data['identity'] = account_data['identity_formatted']
    
    if 'blob_properties_formatted' in account_data:
        account_data['blob_properties'] = account_data['blob_properties_formatted']
    
    if 'static_website_formatted' in account_data:
        account_data['static_website'] = account_data['static_website_formatted']
    
    # Add primary endpoints information
    if hasattr(account_details, 'primary_endpoints') and account_details.primary_endpoints:
        account_data['primary_endpoints'] = {
            "blob": account_details.primary_endpoints.blob,
            "file": account_details.primary_endpoints.file,
            "queue": account_details.primary_endpoints.queue,
            "table": account_details.primary_endpoints.table,
            "web": getattr(account_details.primary_endpoints, 'web', None),
        }

@app.command("scan")
def scan_storage_accounts(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan all dependencies.")
):
    """Scans Azure Storage Accounts and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning Azure Storage Accounts with dependencies...")
        recursive_scan(
            "azure_storage_account",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        typer.echo(f"Scanning for Azure Storage Accounts in subscription '{subscription_id}'...")
        if resource_group_name:
            typer.echo(f"Filtering by resource group: {resource_group_name}")
        if location:
            typer.echo(f"Filtering by location: {location}")
        
        account_data = get_storage_account_data(subscription_id, resource_group_name, location)

        if not account_data:
            typer.echo("No storage accounts found.")
            return

        # Process resources before generating Terraform
        account_data = process_resources(account_data, "azure_storage_account")

        # Generate Terraform files
        generate_tf_auto(account_data, "azure_storage_account", output_dir)

        # Generate import file
        generate_imports_file(
            "azure_storage_account",
            account_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )

@app.command("list")
def list_storage_accounts(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import file")
):
    """List all Azure Storage Account resources previously generated."""
    ImportManager(output_dir, "azure_storage_account").list_all()

@app.command("import")
def import_storage_account(
    account_id: str = typer.Argument(..., help="Azure Storage Account resource ID to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory with import file")
):
    """Run terraform import for a specific Azure Storage Account by its resource ID."""
    ImportManager(output_dir, "azure_storage_account").find_and_import(account_id)

# Scan function for cross-scan registry
def scan_azure_storage_accounts(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None,
    generate_files: bool = True
):
    """Scan function to be registered with cross-scan registry."""
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    typer.echo(f"[Cross-scan] Scanning Azure Storage Accounts in subscription {subscription_id}")
    
    account_data = get_storage_account_data(subscription_id, resource_group_name, location)

    if account_data:
        account_data = process_resources(account_data, "azure_storage_account")
        
        # Only generate files if requested (allows two-phase scanning)
        if generate_files:
            generate_tf_auto(account_data, "azure_storage_account", output_dir)
            generate_imports_file(
                "azure_storage_account",
                account_data,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="azure"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(account_data)} Azure Storage Accounts")
