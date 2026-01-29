"""Azure Automation Accounts scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from terraback.core.license import require_professional

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation

logger = logging.getLogger(__name__)
app = typer.Typer(name="automation", help="Scan and import Azure Automation Accounts and Runbooks.")


@require_professional
def scan_automation_accounts(
    output_dir: Path,
    subscription_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Automation Accounts and generate Terraform configurations.
    
    This function retrieves all Automation Accounts from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        
    Returns:
        List of Automation Account resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    automation_client = get_azure_client('AutomationClient', subscription_id)
    automation_accounts: List[Dict[str, Any]] = []
    runbooks: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Automation Accounts...")
    print("Scanning for Automation Accounts...")
    
    # List all automation accounts with error handling
    @safe_azure_operation("list automation accounts", default_return=[])
    def list_accounts():
        return list(automation_client.automation_account.list())
    
    account_list = list_accounts()
    
    # Process each account
    for account in account_list:
        account_dict = format_resource_dict(account, 'automation_account')
        
        # Format account properties
        _format_account_properties(account_dict, account)
        
        # Get runbooks for this account
        account_runbooks = _get_account_runbooks(
            automation_client, 
            account_dict['resource_group_name'], 
            account.name
        )
        runbooks.extend(account_runbooks)
        
        automation_accounts.append(account_dict)
        logger.debug(f"Processed automation account: {account.name}")
    
    # Generate Terraform files for automation accounts
    if automation_accounts:
        generate_tf_auto(automation_accounts, "azure_automation_account", output_dir, provider="azure")
        
        generate_imports_file(
            "azure_automation_account",
            automation_accounts,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No Automation Accounts found.")
        logger.info("No Automation Accounts found.")
    
    # Generate Terraform files for runbooks
    if runbooks:
        generate_tf_auto(runbooks, "azure_automation_runbook", output_dir)
        
        generate_imports_file(
            "azure_automation_runbook",
            runbooks,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return automation_accounts


def _format_account_properties(account_dict: Dict[str, Any], account: Any) -> None:
    """Format automation account properties."""
    # SKU name
    if hasattr(account, 'sku') and account.sku:
        account_dict['sku_name'] = account.sku.name
    
    # Public network access
    if hasattr(account, 'public_network_access') and account.public_network_access is not None:
        account_dict['public_network_access_enabled'] = account.public_network_access
    
    # Local authentication
    if hasattr(account, 'disable_local_auth') and account.disable_local_auth is not None:
        account_dict['local_authentication_enabled'] = not account.disable_local_auth
    
    # Identity
    if hasattr(account, 'identity') and account.identity:
        account_dict['identity'] = {
            'type': account.identity.type
        }
        if hasattr(account.identity, 'user_assigned_identities') and account.identity.user_assigned_identities:
            account_dict['identity']['identity_ids'] = list(account.identity.user_assigned_identities.keys())
    
    # Encryption
    if hasattr(account, 'encryption') and account.encryption:
        account_dict['encryption'] = {}
        if hasattr(account.encryption, 'key_source') and account.encryption.key_source == 'Microsoft.Keyvault':
            if hasattr(account.encryption, 'key_vault_properties') and account.encryption.key_vault_properties:
                kvp = account.encryption.key_vault_properties
                if hasattr(kvp, 'key_name') and hasattr(kvp, 'key_vault_uri'):
                    account_dict['encryption']['key_vault_key_id'] = f"{kvp.key_vault_uri}keys/{kvp.key_name}"
                if hasattr(kvp, 'key_version') and kvp.key_version:
                    account_dict['encryption']['key_vault_key_id'] += f"/{kvp.key_version}"
            if hasattr(account.encryption, 'identity') and account.encryption.identity:
                account_dict['encryption']['user_assigned_identity_id'] = account.encryption.identity.user_assigned_identity


def _get_account_runbooks(
    automation_client: Any, 
    resource_group: str, 
    account_name: str
) -> List[Dict[str, Any]]:
    """Get all runbooks for a specific automation account."""
    runbooks: List[Dict[str, Any]] = []
    
    @safe_azure_operation(f"list runbooks for account {account_name}", default_return=[])
    def list_runbooks():
        return list(automation_client.runbook.list_by_automation_account(
            resource_group_name=resource_group,
            automation_account_name=account_name
        ))
    
    runbook_list = list_runbooks()
    
    for runbook in runbook_list:
        runbook_dict = format_resource_dict(runbook, 'automation_runbook')
        runbook_dict['automation_account_name'] = account_name
        
        # Format runbook properties
        _format_runbook_properties(runbook_dict, runbook)
        
        # Get detailed runbook content if available
        @safe_azure_operation(f"get runbook content for {runbook.name}", default_return=None)
        def get_runbook_content():
            return automation_client.runbook.get_content(
                resource_group_name=resource_group,
                automation_account_name=account_name,
                runbook_name=runbook.name
            )
        
        content = get_runbook_content()
        if content:
            try:
                # Try to read the content stream
                runbook_dict['content'] = content.read().decode('utf-8')
            except Exception as e:
                logger.warning(f"Could not read content for runbook {runbook.name}: {e}")
        
        runbooks.append(runbook_dict)
        logger.debug(f"Processed runbook: {runbook.name}")
    
    return runbooks


def _format_runbook_properties(runbook_dict: Dict[str, Any], runbook: Any) -> None:
    """Format runbook properties."""
    # Basic properties
    if hasattr(runbook, 'runbook_type'):
        runbook_dict['runbook_type'] = runbook.runbook_type
    
    if hasattr(runbook, 'log_verbose') and runbook.log_verbose is not None:
        runbook_dict['log_verbose'] = runbook.log_verbose
    
    if hasattr(runbook, 'log_progress') and runbook.log_progress is not None:
        runbook_dict['log_progress'] = runbook.log_progress
    
    if hasattr(runbook, 'description'):
        runbook_dict['description'] = runbook.description
    
    # Publish content link
    if hasattr(runbook, 'publish_content_link') and runbook.publish_content_link:
        pcl = runbook.publish_content_link
        runbook_dict['publish_content_link'] = {
            'uri': pcl.uri
        }
        if hasattr(pcl, 'version') and pcl.version:
            runbook_dict['publish_content_link']['version'] = pcl.version
        if hasattr(pcl, 'content_hash') and pcl.content_hash:
            hash_obj = pcl.content_hash
            if hasattr(hash_obj, 'algorithm') and hasattr(hash_obj, 'value'):
                runbook_dict['publish_content_link']['hash'] = {
                    'algorithm': hash_obj.algorithm,
                    'value': hash_obj.value
                }
    
    # Draft properties
    if hasattr(runbook, 'draft') and runbook.draft:
        draft = runbook.draft
        runbook_dict['draft'] = {}
        
        if hasattr(draft, 'in_edit') and draft.in_edit is not None:
            runbook_dict['draft']['edit_mode_enabled'] = draft.in_edit
        
        if hasattr(draft, 'draft_content_link') and draft.draft_content_link:
            dcl = draft.draft_content_link
            runbook_dict['draft']['content_link'] = {
                'uri': dcl.uri
            }
            if hasattr(dcl, 'version') and dcl.version:
                runbook_dict['draft']['content_link']['version'] = dcl.version
            if hasattr(dcl, 'content_hash') and dcl.content_hash:
                hash_obj = dcl.content_hash
                if hasattr(hash_obj, 'algorithm') and hasattr(hash_obj, 'value'):
                    runbook_dict['draft']['content_link']['hash'] = {
                        'algorithm': hash_obj.algorithm,
                        'value': hash_obj.value
                    }
        
        if hasattr(draft, 'parameters') and draft.parameters:
            runbook_dict['draft']['parameters'] = {}
            for param_name, param in draft.parameters.items():
                param_dict = {
                    'type': param.type if hasattr(param, 'type') else 'String'
                }
                if hasattr(param, 'is_mandatory'):
                    param_dict['mandatory'] = param.is_mandatory
                if hasattr(param, 'position'):
                    param_dict['position'] = param.position
                if hasattr(param, 'default_value'):
                    param_dict['default_value'] = param.default_value
                
                runbook_dict['draft']['parameters'][param_name] = param_dict


@app.command("scan")
def scan_automation_accounts_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID.")
):
    """Scans Azure Automation Accounts and Runbooks and generates Terraform code."""
    typer.echo(f"Scanning for Azure Automation Accounts in subscription '{subscription_id}'...")
    
    try:
        scan_automation_accounts(output_dir=output_dir, subscription_id=subscription_id)
    except Exception as e:
        typer.echo(f"Error scanning Automation Accounts: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_automation_accounts(
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Lists all Automation Account resources previously generated."""
    ImportManager(output_dir, "azure_automation_account").list_all()
    ImportManager(output_dir, "azure_automation_runbook").list_all()


@app.command("import")
def import_automation_resource(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Automation resource to import."),
    resource_type: str = typer.Option("account", help="Resource type: 'account' or 'runbook'."),
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Runs terraform import for a specific Automation resource."""
    if resource_type == "account":
        ImportManager(output_dir, "azure_automation_account").find_and_import(resource_id)
    elif resource_type == "runbook":
        ImportManager(output_dir, "azure_automation_runbook").find_and_import(resource_id)
    else:
        typer.echo(f"Invalid resource type: {resource_type}. Use 'account' or 'runbook'.", err=True)
        raise typer.Exit(code=1)