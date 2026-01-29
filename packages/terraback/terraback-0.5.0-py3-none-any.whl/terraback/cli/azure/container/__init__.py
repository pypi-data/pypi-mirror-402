"""Azure container services module."""
from terraback.utils.cross_scan_registry import register_resource_scanner

import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="container",
    help="Work with Azure Container resources (ACR, AKS).",
    no_args_is_help=True
)

def register():
    """Register container resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Container Registries
    register_resource_scanner(
        resource_type="azure_container_registry",
        scanner_function="terraback.cli.azure.container.container_registries:scan_container_registries",
        priority=20,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_container_registry", "azure_resource_group")
    
    # AKS Clusters
    register_resource_scanner(
        resource_type="azure_kubernetes_cluster",
        scanner_function="terraback.cli.azure.container.aks_clusters:scan_aks_clusters",
        priority=30,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_kubernetes_cluster", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_kubernetes_cluster", "azure_virtual_network")
    cross_scan_registry.register_dependency("azure_kubernetes_cluster", "azure_subnet")

# Import modules for CLI commands
from . import container_registries, aks_clusters

# Add CLI commands if available
if hasattr(container_registries, 'app'):
    app.add_typer(container_registries.app, name="acr", help="Azure Container Registry management")

if hasattr(aks_clusters, 'app'):
    app.add_typer(aks_clusters.app, name="aks", help="Azure Kubernetes Service management")

@app.command("scan-all")
def scan_all_container(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
):
    """Scan all Azure Container resources."""
    from terraback.cli.azure.session import get_default_subscription_id
    from .container_registries import scan_container_registries
    from .aks_clusters import scan_aks_clusters
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning all container resources in subscription '{subscription_id}'...")
    
    # Scan Container Registries
    typer.echo("\n=== Scanning Container Registries ===")
    scan_container_registries(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )
    
    # Scan AKS Clusters
    typer.echo("\n=== Scanning AKS Clusters ===")
    scan_aks_clusters(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )
    
    typer.echo("\nContainer scanning complete!")