# terraback/cli/azure/network/__init__.py
import typer
from pathlib import Path
from typing import Optional

from . import vnets, subnets, nsgs, network_interfaces, public_ips
from .vnets import scan_azure_vnets
from .subnets import scan_azure_subnets
from .nsgs import scan_azure_nsgs
from .network_interfaces import scan_azure_network_interfaces
from .public_ips import scan_public_ips
from terraback.utils.cross_scan_registry import register_resource_scanner, cross_scan_registry

app = typer.Typer(
    name="network",
    help="Work with Azure Networking resources like VNets, Subnets, NSGs, and NICs.",
    no_args_is_help=True
)

def register():
    """Registers the network resources with the cross-scan registry."""
    # Virtual Networks
    register_resource_scanner(
        resource_type="azure_virtual_network",
        scanner_function="terraback.cli.azure.network.vnets:scan_azure_vnets",
        priority=10
    )
    
    # Subnets
    register_resource_scanner(
        resource_type="azure_subnet",
        scanner_function="terraback.cli.azure.network.subnets:scan_azure_subnets",
        priority=11
    )
    
    # Network Security Groups
    register_resource_scanner(
        resource_type="azure_network_security_group",
        scanner_function="terraback.cli.azure.network.nsgs:scan_azure_nsgs",
        priority=12
    )
    
    # Network Interfaces
    register_resource_scanner(
        resource_type="azure_network_interface",
        scanner_function="terraback.cli.azure.network.network_interfaces:scan_azure_network_interfaces",
        priority=13
    )
    
    # Public IPs - No tier requirement (matches AWS Elastic IPs)
    from terraback.core.license import Tier
    register_resource_scanner(
        resource_type="azure_public_ip",
        scanner_function="terraback.cli.azure.network.public_ips:scan_public_ips",
        priority=15
    )
    
    # NAT Gateways - No tier requirement (matches AWS NAT Gateways)
    register_resource_scanner(
        resource_type="azure_nat_gateway",
        scanner_function="terraback.cli.azure.network.nat_gateways:scan_nat_gateways",
        priority=16
    )
    
    # Route Tables - No tier requirement (matches AWS Route Tables)
    register_resource_scanner(
        resource_type="azure_route_table",
        scanner_function="terraback.cli.azure.network.route_tables:scan_route_tables",
        priority=17
    )
    
    # VNet Dependencies
    cross_scan_registry.register_dependency("azure_virtual_network", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_virtual_network", "azure_subnet")
    
    # Subnet dependencies
    cross_scan_registry.register_dependency("azure_subnet", "azure_virtual_network")
    cross_scan_registry.register_dependency("azure_subnet", "azure_network_security_group")
    cross_scan_registry.register_dependency("azure_subnet", "azure_route_table")
    
    # NSG dependencies  
    cross_scan_registry.register_dependency("azure_network_security_group", "azure_resource_group")
    
    # Network Interface dependencies
    cross_scan_registry.register_dependency("azure_network_interface", "azure_subnet")
    cross_scan_registry.register_dependency("azure_network_interface", "azure_network_security_group")
    cross_scan_registry.register_dependency("azure_network_interface", "azure_lb")
    
    # Public IP dependencies
    cross_scan_registry.register_dependency("azure_public_ip", "azure_resource_group")
    
    # NAT Gateway dependencies
    cross_scan_registry.register_dependency("azure_nat_gateway", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_nat_gateway", "azure_public_ip")
    
    # Route Table dependencies
    cross_scan_registry.register_dependency("azure_route_table", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_subnet", "azure_route_table")

# Add sub-commands
app.add_typer(vnets.app, name="vnet")
app.add_typer(subnets.app, name="subnet")
app.add_typer(nsgs.app, name="nsg")
app.add_typer(network_interfaces.app, name="nic")

# Import public_ips_cli separately to avoid circular import
from .public_ips_cli import app as public_ips_app
app.add_typer(public_ips_app, name="public-ip")

# Add convenience command for scanning all network resources
@app.command("scan-all")
def scan_all_network(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies")
):
    """Scan all Azure network resources."""
    from terraback.cli.azure.session import get_default_subscription_id
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan(
            "azure_virtual_network",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        # Scan VNets
        vnets.scan_vnets(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            with_deps=False
        )
        
        # Scan Subnets
        subnets.scan_subnets(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            with_deps=False
        )
        
        # Scan NSGs
        nsgs.scan_nsgs(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            with_deps=False
        )
        
        # Scan NICs
        network_interfaces.scan_network_interfaces(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            with_deps=False
        )
