"""Azure Container Registry scanning and management module."""

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
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="container-registry", help="Scan and import Azure Container Registries.")

@require_professional
def scan_container_registries(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Container Registries and generate Terraform configurations.
    
    This function retrieves all Container Registries from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of Container Registry resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    acr_client = get_azure_client('ContainerRegistryManagementClient', subscription_id)
    registries: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure Container Registries...")
    print("Scanning for Container Registries...")
    
    # List all container registries with error handling
    @safe_azure_operation("list container registries", default_return=[])
    def list_registries():
        if resource_group_name:
            return list(acr_client.registries.list_by_resource_group(resource_group_name))
        else:
            return list(acr_client.registries.list())
    
    registry_list = list_registries()
    
    # Process each registry
    for registry in registry_list:
        registry_dict = format_resource_dict(registry, 'container_registry')
        
        # Format SKU information
        _format_sku(registry_dict, registry)
        
        # Format network rule set
        _format_network_rules(registry_dict, registry)
        
        # Format policies
        _format_policies(registry_dict, registry)
        
        # Format encryption settings
        _format_encryption(registry_dict, registry)
        
        # Format all template attributes
        _format_template_attributes(registry_dict, registry)
        
        # Get webhooks
        webhooks = _get_webhooks(acr_client, registry_dict, registry.name)
        if webhooks:
            registry_dict['webhooks'] = webhooks
        
        # Get replications
        replications = _get_replications(acr_client, registry_dict, registry.name, registry.location)
        if replications:
            registry_dict['georeplications'] = replications
        
        registries.append(registry_dict)
        logger.debug(f"Processed container registry: {registry.name}")    # Process resources before generation
    registries = process_resources(registries, "azure_container_registry")
    

    
    # Generate Terraform files
    if registries:
        generate_tf_auto(registries, "azure_container_registry", output_dir)
        
        generate_imports_file(
            "azure_container_registry",
            registries,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No Container Registries found.")
        logger.info("No Container Registries found.")
    
    return registries

def _format_sku(registry_dict: Dict[str, Any], registry: Any) -> None:
    """Format SKU information for the registry."""
    if hasattr(registry, 'sku') and registry.sku:
        registry_dict['sku'] = registry.sku.name
        registry_dict['sku_tier'] = registry.sku.tier


def _format_network_rules(registry_dict: Dict[str, Any], registry: Any) -> None:
    """Format network rule set for the registry."""
    if not hasattr(registry, 'network_rule_set') or not registry.network_rule_set:
        return
        
    nrs = registry.network_rule_set
    registry_dict['network_rule_set_formatted'] = {
        'default_action': nrs.default_action,
        'ip_rules': [
            {'ip_address_or_range': rule.value}
            for rule in (nrs.ip_rules or [])
        ],
        'virtual_network_rules': [
            {'subnet_id': rule.virtual_network_resource_id}
            for rule in (nrs.virtual_network_rules or [])
        ]
    }


def _format_policies(registry_dict: Dict[str, Any], registry: Any) -> None:
    """Format policies for the registry."""
    if not hasattr(registry, 'policies') or not registry.policies:
        return
        
    policies = registry.policies
    
    # Retention policy
    if hasattr(policies, 'retention_policy') and policies.retention_policy:
        rp = policies.retention_policy
        registry_dict['retention_policy_formatted'] = {
            'enabled': rp.status == 'enabled',
            'days': rp.days
        }
    
    # Trust policy
    if hasattr(policies, 'trust_policy') and policies.trust_policy:
        tp = policies.trust_policy
        registry_dict['trust_policy_formatted'] = {
            'enabled': tp.status == 'enabled'
        }
        
    # Quarantine policy
    if hasattr(policies, 'quarantine_policy') and policies.quarantine_policy:
        qp = policies.quarantine_policy
        registry_dict['quarantine_policy_enabled'] = qp.status == 'enabled'
        
    # Export policy  
    if hasattr(policies, 'export_policy') and policies.export_policy:
        ep = policies.export_policy
        registry_dict['export_policy_enabled'] = ep.status == 'enabled'


def _format_encryption(registry_dict: Dict[str, Any], registry: Any) -> None:
    """Format encryption settings for the registry."""
    if not hasattr(registry, 'encryption') or not registry.encryption:
        return
        
    enc = registry.encryption
    registry_dict['encryption_formatted'] = {
        'enabled': enc.status == 'enabled',
        'key_vault_key_id': enc.key_vault_properties.key_identifier if enc.key_vault_properties else None
    }


def _format_template_attributes(registry_dict: Dict[str, Any], registry: Any) -> None:
    """Format all registry attributes to match Jinja2 template expectations."""
    
    # Map basic boolean attributes from Azure API to template-compatible names
    if hasattr(registry, 'admin_user_enabled'):
        registry_dict['admin_enabled'] = registry.admin_user_enabled
    
    # Convert public_network_access from string to boolean
    if hasattr(registry, 'public_network_access'):
        registry_dict['public_network_access_enabled'] = registry.public_network_access == 'Enabled'
    
    # Map network rule bypass option 
    if hasattr(registry, 'network_rule_bypass_options'):
        registry_dict['network_rule_bypass_option'] = registry.network_rule_bypass_options
    
    # Convert zone_redundancy from string to boolean
    if hasattr(registry, 'zone_redundancy'):
        registry_dict['zone_redundancy_enabled'] = registry.zone_redundancy == 'Enabled'
    
    # Map data endpoint settings
    if hasattr(registry, 'data_endpoint_enabled'):
        registry_dict['data_endpoint_enabled'] = registry.data_endpoint_enabled
    
    # Add missing attributes that should be in template
    if hasattr(registry, 'login_server'):
        registry_dict['login_server'] = registry.login_server
        
    # Map SKU attributes
    if hasattr(registry, 'sku'):
        if hasattr(registry.sku, 'tier'):
            registry_dict['sku_tier'] = registry.sku.tier
            
    # Handle tags - ensure empty tags are handled properly
    if not hasattr(registry, 'tags') or not registry.tags:
        registry_dict['tags'] = {}
    else:
        registry_dict['tags'] = dict(registry.tags) if registry.tags else {}
    
    # Set policy defaults if not exists
    if 'retention_policy_formatted' not in registry_dict:
        registry_dict['retention_policy_formatted'] = {'enabled': False, 'days': 7}
        
    if 'trust_policy_formatted' not in registry_dict:
        registry_dict['trust_policy_formatted'] = {'enabled': False}
        
    if 'encryption_formatted' not in registry_dict:
        registry_dict['encryption_formatted'] = {'enabled': False, 'key_vault_key_id': None}


def _get_webhooks(
    acr_client: Any,
    registry_dict: Dict[str, Any],
    registry_name: str
) -> List[Dict[str, Any]]:
    """Get webhooks for the registry with error handling."""
    @safe_azure_operation(f"list webhooks for {registry_name}", default_return=[])
    def list_webhooks():
        webhooks = list(acr_client.webhooks.list(
            resource_group_name=registry_dict['resource_group_name'],
            registry_name=registry_name
        ))
        return [
            {
                'name': webhook.name,
                'service_uri': webhook.config.service_uri if webhook.config else None,
                'actions': webhook.config.actions if webhook.config else [],
                'status': webhook.status,
                'scope': webhook.scope
            }
            for webhook in webhooks
        ]
    
    return list_webhooks()


def _get_replications(
    acr_client: Any,
    registry_dict: Dict[str, Any],
    registry_name: str,
    home_location: str
) -> List[Dict[str, Any]]:
    """Get replications for the registry with error handling."""
    @safe_azure_operation(f"list replications for {registry_name}", default_return=[])
    def list_replications():
        replications = list(acr_client.replications.list(
            resource_group_name=registry_dict['resource_group_name'],
            registry_name=registry_name
        ))
        return [
            {
                'location': repl.location,
                'tags': repl.tags or {}
            }
            for repl in replications
            if repl.location != home_location  # Exclude home location
        ]
    
    return list_replications()


# CLI Commands
@app.command("scan")
def scan_container_registries_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure Container Registries and generates Terraform code."""
    typer.echo(f"Scanning for Azure Container Registries in subscription '{subscription_id}'...")
    
    try:
        scan_container_registries(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning Container Registries: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_container_registries(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all Container Registry resources previously generated."""
    ImportManager(output_dir, "azure_container_registry").list_all()


@app.command("import")
def import_container_registry(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Container Registry to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific Container Registry."""
    ImportManager(output_dir, "azure_container_registry").find_and_import(resource_id)
