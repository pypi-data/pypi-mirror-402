# terraback/cli/azure/network/vnets.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import AzureError

from terraback.cli.azure.session import get_cached_azure_session, get_default_subscription_id
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.resource_processor import process_resources
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
import logging

logger = logging.getLogger(__name__)

app = typer.Typer(name="vnet", help="Scan and import Azure Virtual Networks.")

def get_vnet_data(subscription_id: str = None, resource_group_name: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Virtual Network data from Azure.
    
    Args:
        subscription_id: Azure subscription ID (optional)
        resource_group_name: Optional resource group filter
        location: Optional location filter
    
    Returns:
        List of VNet data dictionaries
    """
    session = get_cached_azure_session(subscription_id)
    network_client = NetworkManagementClient(**session)
    
    vnets = []
    
    try:
        # Get VNets either from specific resource group or all with error handling
        @safe_azure_operation("list virtual networks", default_return=[])
        def list_vnets():
            if resource_group_name:
                return list(network_client.virtual_networks.list(resource_group_name))
            else:
                return list(network_client.virtual_networks.list_all())
        
        vnet_list = list_vnets()
        
        for vnet in vnet_list:
            # Apply location filter if specified
            if location and vnet.location != location:
                continue
                
            # Parse resource group from ID
            rg_name = vnet.id.split('/')[4]
            
            # Use the common format_resource_dict function
            vnet_data = format_resource_dict(vnet, 'virtual_network')
            
            # Add basic fields that might not be in format_resource_dict
            vnet_data.update({
                "name": vnet.name,
                "id": vnet.id,
                "resource_group_name": rg_name,
                "location": vnet.location,
            })
            
            # Format address space
            _format_address_space(vnet_data, vnet)
            
            # Format DNS servers
            _format_dns_servers(vnet_data, vnet)
            
            # Format subnet information
            _format_subnet_info(vnet_data, vnet)
            
            # Format DDoS protection
            _format_ddos_protection(vnet_data, vnet)
            
            # Format other properties
            _format_other_vnet_properties(vnet_data, vnet)
            
            # Format all template attributes
            _format_template_attributes(vnet_data, vnet)
            
            vnets.append(vnet_data)
            
    except AzureError as e:
        typer.echo(f"Error fetching VNets: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return vnets

@app.command("scan")
def scan_vnets(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan all dependencies (Subnets, NSGs, etc.).")
):
    """Scans Azure Virtual Networks and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning Azure VNets with dependencies...")
        recursive_scan(
            "azure_virtual_network",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        typer.echo(f"Scanning for Azure VNets in subscription '{subscription_id}'...")
        if resource_group_name:
            typer.echo(f"Filtering by resource group: {resource_group_name}")
        if location:
            typer.echo(f"Filtering by location: {location}")
        
        vnet_data = get_vnet_data(subscription_id, resource_group_name, location)

        if not vnet_data:
            typer.echo("No VNets found.")
            return

        vnet_data = process_resources(vnet_data, "azure_virtual_network")

        # Generate Terraform files
        generate_tf_auto(vnet_data, "azure_virtual_network", output_dir)

        # Generate import file
        generate_imports_file(
            "azure_virtual_network",
            vnet_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )

@app.command("list")
def list_vnets(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import file")
):
    """List all Azure VNet resources previously generated."""
    ImportManager(output_dir, "azure_virtual_network").list_all()

@app.command("import")
def import_vnet(
    vnet_id: str = typer.Argument(..., help="Azure VNet resource ID to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory with import file")
):
    """Run terraform import for a specific Azure VNet by its resource ID."""
    ImportManager(output_dir, "azure_virtual_network").find_and_import(vnet_id)

# Scan function for cross-scan registry
def scan_azure_vnets(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan function to be registered with cross-scan registry."""
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    typer.echo(f"[Cross-scan] Scanning Azure VNets in subscription {subscription_id}")
    
    vnet_data = get_vnet_data(subscription_id, resource_group_name, location)

    if vnet_data:
        vnet_data = process_resources(vnet_data, "azure_virtual_network")
        generate_tf_auto(vnet_data, "azure_virtual_network", output_dir)
        generate_imports_file(
            "azure_virtual_network",
            vnet_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(vnet_data)} Azure VNets")


def _format_address_space(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format address space for the virtual network."""
    if hasattr(vnet, 'address_space') and vnet.address_space:
        vnet_data['address_space'] = vnet.address_space.address_prefixes or []
    else:
        vnet_data['address_space'] = []


def _format_dns_servers(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format DNS servers for the virtual network."""
    if hasattr(vnet, 'dhcp_options') and vnet.dhcp_options and vnet.dhcp_options.dns_servers:
        vnet_data['dns_servers'] = vnet.dhcp_options.dns_servers
    else:
        vnet_data['dns_servers'] = []


def _format_subnet_info(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format subnet information for the virtual network."""
    vnet_data['subnet_names'] = []
    vnet_data['subnet_count'] = 0
    vnet_data['subnet_details'] = []
    
    if hasattr(vnet, 'subnets') and vnet.subnets:
        vnet_data['subnet_names'] = [subnet.name for subnet in vnet.subnets]
        vnet_data['subnet_count'] = len(vnet.subnets)
        
        # Add subnet details for reference (but not full subnet resources)
        for subnet in vnet.subnets:
            vnet_data['subnet_details'].append({
                'name': subnet.name,
                'address_prefix': subnet.address_prefix,
                'id': subnet.id,
            })


def _format_ddos_protection(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format DDoS protection settings for the virtual network."""
    if hasattr(vnet, 'ddos_protection_plan') and vnet.ddos_protection_plan:
        vnet_data['ddos_protection_plan'] = {
            'id': vnet.ddos_protection_plan.id,
            'enable': True
        }
    else:
        vnet_data['ddos_protection_plan'] = None


def _format_other_vnet_properties(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format other properties for the virtual network."""
    # BGP community
    if hasattr(vnet, 'bgp_communities') and vnet.bgp_communities:
        vnet_data['bgp_community'] = vnet.bgp_communities.virtual_network_community
    else:
        vnet_data['bgp_community'] = None
    
    # VM protection
    if hasattr(vnet, 'enable_vm_protection'):
        vnet_data['vm_protection_enabled'] = vnet.enable_vm_protection
    else:
        vnet_data['vm_protection_enabled'] = None
    
    # Flow timeout
    if hasattr(vnet, 'flow_timeout_in_minutes'):
        vnet_data['flow_timeout_in_minutes'] = vnet.flow_timeout_in_minutes
    else:
        vnet_data['flow_timeout_in_minutes'] = None
    
    # Provisioning state
    if hasattr(vnet, 'provisioning_state'):
        vnet_data['provisioning_state'] = vnet.provisioning_state


def _format_template_attributes(vnet_data: Dict[str, Any], vnet: Any) -> None:
    """Format all VNet attributes to match Jinja2 template expectations."""
    
    # Handle tags - ensure empty tags are handled properly
    if not hasattr(vnet, 'tags') or not vnet.tags:
        vnet_data['tags'] = {}
    else:
        vnet_data['tags'] = dict(vnet.tags) if vnet.tags else {}
    
    # Set sanitized name for resource naming
    vnet_data['name_sanitized'] = vnet.name.replace('-', '_').replace('.', '_').lower()
    
    # Ensure address_space is always a list
    if 'address_space' not in vnet_data or not isinstance(vnet_data['address_space'], list):
        vnet_data['address_space'] = []
    
    # Ensure dns_servers is always a list
    if 'dns_servers' not in vnet_data or not isinstance(vnet_data['dns_servers'], list):
        vnet_data['dns_servers'] = []
    
    # Set default boolean values
    if 'vm_protection_enabled' not in vnet_data or vnet_data['vm_protection_enabled'] is None:
        vnet_data['vm_protection_enabled'] = False
