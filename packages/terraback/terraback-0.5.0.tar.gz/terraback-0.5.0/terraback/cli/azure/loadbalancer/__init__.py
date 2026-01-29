# terraback/cli/azure/loadbalancer/__init__.py
import typer
from pathlib import Path
from typing import Optional

from . import load_balancers, application_gateways
from .load_balancers import scan_azure_load_balancers
from terraback.utils.cross_scan_registry import register_resource_scanner, cross_scan_registry

app = typer.Typer(
    name="lb",
    help="Work with Azure Load Balancers.",
    no_args_is_help=True
)

def register():
    """Registers the load balancer resources with the cross-scan registry."""
    from terraback.core.license import Tier
    
    # Load Balancers
    register_resource_scanner(
        resource_type="azure_lb",
        scanner_function="terraback.cli.azure.loadbalancer.load_balancers:scan_azure_load_balancers",
        priority=20
    )
    
    # Load Balancer Dependencies
    cross_scan_registry.register_dependency("azure_lb", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_lb", "azure_virtual_network")
    cross_scan_registry.register_dependency("azure_lb", "azure_subnet")
    
    # Application Gateways
    register_resource_scanner(
        resource_type="azure_application_gateway",
        scanner_function="terraback.cli.azure.loadbalancer.application_gateways:scan_application_gateways",
        priority=25,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_application_gateway", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_application_gateway", "azure_virtual_network")
    cross_scan_registry.register_dependency("azure_application_gateway", "azure_subnet")
    cross_scan_registry.register_dependency("azure_application_gateway", "azure_public_ip")

# Add sub-commands
app.add_typer(load_balancers.app, name="standard")
app.add_typer(application_gateways.app, name="app-gateway")

# Add convenience command for scanning all load balancer resources
@app.command("scan-all")
def scan_all_lb(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies")
):
    """Scan all Azure Load Balancer resources."""
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
            "azure_lb",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        # Scan Load Balancers
        load_balancers.scan_load_balancers(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            with_deps=False
        )

from terraback.core.license import require_professional

@require_professional
def scan_azure_application_gateways(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Application Gateways (Professional feature)."""
    from .application_gateways import scan_application_gateways
    scan_application_gateways(
        output_dir=output_dir,
        subscription_id=subscription_id
    )
