"""Azure Event Hubs scanning and management module."""

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
app = typer.Typer(name="event-hubs", help="Scan and import Azure Event Hubs.")


@require_professional
def scan_event_hubs(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None  # Accept but ignore location parameter for compatibility
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Event Hubs and generate Terraform configurations.
    
    This function retrieves all Event Hub Namespaces and Event Hubs from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        
    Returns:
        List of Event Hub resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    eventhub_client = get_azure_client('EventHubManagementClient', subscription_id)
    namespaces: List[Dict[str, Any]] = []
    event_hubs: List[Dict[str, Any]] = []
    consumer_groups: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Event Hub Namespaces...")
    print("Scanning for Event Hub Namespaces...")
    
    # List all event hub namespaces with error handling
    @safe_azure_operation("list event hub namespaces", default_return=[])
    def list_namespaces():
        return list(eventhub_client.namespaces.list())
    
    namespace_list = list_namespaces()
    
    # Process each namespace
    for namespace in namespace_list:
        namespace_dict = format_resource_dict(namespace, 'eventhub_namespace')
        
        # Format namespace properties
        _format_namespace_properties(namespace_dict, namespace)
        
        # Get event hubs for this namespace
        namespace_event_hubs = _get_namespace_event_hubs(
            eventhub_client, 
            namespace_dict['resource_group_name'], 
            namespace.name
        )
        
        # Get consumer groups for each event hub
        for eh in namespace_event_hubs:
            eh_consumer_groups = _get_event_hub_consumer_groups(
                eventhub_client,
                namespace_dict['resource_group_name'],
                namespace.name,
                eh['name']
            )
            consumer_groups.extend(eh_consumer_groups)
        
        event_hubs.extend(namespace_event_hubs)
        namespaces.append(namespace_dict)
        logger.debug(f"Processed event hub namespace: {namespace.name}")
    
    # Process resources before generation
    namespaces = process_resources(namespaces, "azure_eventhub_namespace")
    
    # Generate Terraform files for namespaces
    if namespaces:
        generate_tf_auto(namespaces, "azure_eventhub_namespace", output_dir)
        
        generate_imports_file(
            "azure_eventhub_namespace",
            namespaces,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No Event Hub Namespaces found.")
        logger.info("No Event Hub Namespaces found.")
    
    # Process event hubs before generation
    event_hubs = process_resources(event_hubs, "azure_eventhub")
    
    # Generate Terraform files for event hubs
    if event_hubs:
        generate_tf_auto(event_hubs, "azure_eventhub", output_dir)
        
        generate_imports_file(
            "azure_eventhub",
            event_hubs,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    # Generate Terraform files for consumer groups
    if consumer_groups:
        generate_tf_auto(consumer_groups, "azure_eventhub_consumer_group", output_dir)
        
        generate_imports_file(
            "azure_eventhub_consumer_group",
            consumer_groups,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return namespaces


def _format_namespace_properties(namespace_dict: Dict[str, Any], namespace: Any) -> None:
    """Format event hub namespace properties."""
    # SKU
    if hasattr(namespace, 'sku') and namespace.sku:
        namespace_dict['sku'] = namespace.sku.name
        if hasattr(namespace.sku, 'capacity'):
            namespace_dict['capacity'] = namespace.sku.capacity
    
    # Auto-inflate
    if hasattr(namespace, 'is_auto_inflate_enabled') and namespace.is_auto_inflate_enabled is not None:
        namespace_dict['auto_inflate_enabled'] = namespace.is_auto_inflate_enabled
        if namespace.is_auto_inflate_enabled and hasattr(namespace, 'maximum_throughput_units'):
            namespace_dict['maximum_throughput_units'] = namespace.maximum_throughput_units
    
    # Zone redundant
    if hasattr(namespace, 'zone_redundant') and namespace.zone_redundant is not None:
        namespace_dict['zone_redundant'] = namespace.zone_redundant
    
    # Network rules
    if hasattr(namespace, 'network_rule_set') and namespace.network_rule_set:
        nrs = namespace.network_rule_set
        namespace_dict['network_rulesets'] = [{
            'default_action': nrs.default_action if hasattr(nrs, 'default_action') else 'Deny',
            'trusted_service_access_enabled': nrs.trusted_service_access_enabled if hasattr(nrs, 'trusted_service_access_enabled') else False
        }]
        
        # IP rules
        if hasattr(nrs, 'ip_rules') and nrs.ip_rules:
            namespace_dict['network_rulesets'][0]['ip_rule'] = []
            for rule in nrs.ip_rules:
                namespace_dict['network_rulesets'][0]['ip_rule'].append({
                    'ip_mask': rule.ip_mask,
                    'action': rule.action if hasattr(rule, 'action') else 'Allow'
                })
        
        # Virtual network rules
        if hasattr(nrs, 'virtual_network_rules') and nrs.virtual_network_rules:
            namespace_dict['network_rulesets'][0]['virtual_network_rule'] = []
            for rule in nrs.virtual_network_rules:
                namespace_dict['network_rulesets'][0]['virtual_network_rule'].append({
                    'subnet_id': rule.subnet.id if rule.subnet else None,
                    'ignore_missing_virtual_network_service_endpoint': rule.ignore_missing_virtual_network_service_endpoint if hasattr(rule, 'ignore_missing_virtual_network_service_endpoint') else False
                })
    
    # Identity
    if hasattr(namespace, 'identity') and namespace.identity:
        namespace_dict['identity'] = {
            'type': namespace.identity.type
        }
        if hasattr(namespace.identity, 'user_assigned_identities') and namespace.identity.user_assigned_identities:
            namespace_dict['identity']['identity_ids'] = list(namespace.identity.user_assigned_identities.keys())
    
    # Encryption
    if hasattr(namespace, 'encryption') and namespace.encryption:
        namespace_dict['encryption'] = {}
        if hasattr(namespace.encryption, 'key_source') and namespace.encryption.key_source == 'Microsoft.KeyVault':
            if hasattr(namespace.encryption, 'key_vault_properties') and namespace.encryption.key_vault_properties:
                for kvp in namespace.encryption.key_vault_properties:
                    if hasattr(kvp, 'key_name') and hasattr(kvp, 'key_vault_uri'):
                        namespace_dict['encryption']['key_vault_key_id'] = f"{kvp.key_vault_uri}keys/{kvp.key_name}"
                        if hasattr(kvp, 'key_version') and kvp.key_version:
                            namespace_dict['encryption']['key_vault_key_id'] += f"/{kvp.key_version}"
                        break


def _get_namespace_event_hubs(
    eventhub_client: Any, 
    resource_group: str, 
    namespace_name: str
) -> List[Dict[str, Any]]:
    """Get all event hubs for a specific namespace."""
    event_hubs: List[Dict[str, Any]] = []
    
    @safe_azure_operation(f"list event hubs for namespace {namespace_name}", default_return=[])
    def list_event_hubs():
        return list(eventhub_client.event_hubs.list_by_namespace(
            resource_group_name=resource_group,
            namespace_name=namespace_name
        ))
    
    event_hub_list = list_event_hubs()
    
    for event_hub in event_hub_list:
        eh_dict = format_resource_dict(event_hub, 'eventhub')
        eh_dict['namespace_name'] = namespace_name
        
        # Format event hub properties
        _format_event_hub_properties(eh_dict, event_hub)
        
        event_hubs.append(eh_dict)
        logger.debug(f"Processed event hub: {event_hub.name}")
    
    return event_hubs


def _format_event_hub_properties(eh_dict: Dict[str, Any], event_hub: Any) -> None:
    """Format event hub properties."""
    # Partition count
    if hasattr(event_hub, 'partition_count'):
        eh_dict['partition_count'] = event_hub.partition_count
    
    # Message retention
    if hasattr(event_hub, 'message_retention_in_days'):
        eh_dict['message_retention_in_days'] = event_hub.message_retention_in_days
    
    # Capture settings
    if hasattr(event_hub, 'capture_description') and event_hub.capture_description:
        capture = event_hub.capture_description
        eh_dict['capture_description'] = {
            'enabled': capture.enabled if hasattr(capture, 'enabled') else False
        }
        
        if hasattr(capture, 'encoding'):
            eh_dict['capture_description']['encoding'] = capture.encoding
        
        if hasattr(capture, 'interval_in_seconds'):
            eh_dict['capture_description']['interval_in_seconds'] = capture.interval_in_seconds
        
        if hasattr(capture, 'size_limit_in_bytes'):
            eh_dict['capture_description']['size_limit_in_bytes'] = capture.size_limit_in_bytes
        
        if hasattr(capture, 'skip_empty_archives') and capture.skip_empty_archives is not None:
            eh_dict['capture_description']['skip_empty_archives'] = capture.skip_empty_archives
        
        # Destination
        if hasattr(capture, 'destination') and capture.destination:
            dest = capture.destination
            eh_dict['capture_description']['destination'] = {
                'name': dest.name if hasattr(dest, 'name') else 'EventHubArchive.AzureBlockBlob'
            }
            
            if hasattr(dest, 'blob_container'):
                eh_dict['capture_description']['destination']['blob_container_name'] = dest.blob_container
            
            if hasattr(dest, 'storage_account_resource_id'):
                eh_dict['capture_description']['destination']['storage_account_id'] = dest.storage_account_resource_id
            
            if hasattr(dest, 'archive_name_format'):
                eh_dict['capture_description']['destination']['archive_name_format'] = dest.archive_name_format


def _get_event_hub_consumer_groups(
    eventhub_client: Any,
    resource_group: str,
    namespace_name: str,
    event_hub_name: str
) -> List[Dict[str, Any]]:
    """Get all consumer groups for a specific event hub."""
    consumer_groups: List[Dict[str, Any]] = []
    
    @safe_azure_operation(f"list consumer groups for event hub {event_hub_name}", default_return=[])
    def list_consumer_groups():
        return list(eventhub_client.consumer_groups.list_by_event_hub(
            resource_group_name=resource_group,
            namespace_name=namespace_name,
            event_hub_name=event_hub_name
        ))
    
    cg_list = list_consumer_groups()
    
    for cg in cg_list:
        # Skip the default consumer group
        if cg.name == '$Default':
            continue
            
        cg_dict = format_resource_dict(cg, 'eventhub_consumer_group')
        cg_dict['namespace_name'] = namespace_name
        cg_dict['eventhub_name'] = event_hub_name
        
        # User metadata
        if hasattr(cg, 'user_metadata'):
            cg_dict['user_metadata'] = cg.user_metadata
        
        consumer_groups.append(cg_dict)
        logger.debug(f"Processed consumer group: {cg.name}")
    
    return consumer_groups


@app.command("scan")
def scan_event_hubs_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID.")
):
    """Scans Azure Event Hubs and generates Terraform code."""
    typer.echo(f"Scanning for Azure Event Hubs in subscription '{subscription_id}'...")
    
    try:
        scan_event_hubs(output_dir=output_dir, subscription_id=subscription_id)
    except Exception as e:
        typer.echo(f"Error scanning Event Hubs: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_event_hubs(
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Lists all Event Hub resources previously generated."""
    ImportManager(output_dir, "azure_eventhub_namespace").list_all()
    ImportManager(output_dir, "azure_eventhub").list_all()
    ImportManager(output_dir, "azure_eventhub_consumer_group").list_all()


@app.command("import")
def import_event_hub_resource(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Event Hub resource to import."),
    resource_type: str = typer.Option("namespace", help="Resource type: 'namespace', 'eventhub', or 'consumer_group'."),
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Runs terraform import for a specific Event Hub resource."""
    if resource_type == "namespace":
        ImportManager(output_dir, "azure_eventhub_namespace").find_and_import(resource_id)
    elif resource_type == "eventhub":
        ImportManager(output_dir, "azure_eventhub").find_and_import(resource_id)
    elif resource_type == "consumer_group":
        ImportManager(output_dir, "azure_eventhub_consumer_group").find_and_import(resource_id)
    else:
        typer.echo(f"Invalid resource type: {resource_type}. Use 'namespace', 'eventhub', or 'consumer_group'.", err=True)
        raise typer.Exit(code=1)