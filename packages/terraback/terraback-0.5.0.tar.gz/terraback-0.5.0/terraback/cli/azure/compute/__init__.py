import typer
from pathlib import Path
from functools import partial
from typing import Optional

from . import virtual_machines, disks, ssh_keys, vmss
from .virtual_machines import scan_azure_vms
from .disks import scan_azure_disks
from .vmss import scan_vm_scale_sets
from terraback.utils.cross_scan_registry import register_resource_scanner, cross_scan_registry

app = typer.Typer(
    name="compute",
    help="Work with Azure Compute resources like VMs, Disks, and SSH Keys.",
    no_args_is_help=True
)

def register():
    """
    Registers the Azure compute resources with the cross-scan registry.
    """
    # Virtual Machines
    register_resource_scanner(
        resource_type="azure_virtual_machine",
        scanner_function="terraback.cli.azure.compute.virtual_machines:scan_azure_vms",
        priority=15
    )
    
    # VM Dependencies
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_network_interface")
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_subnet")
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_managed_disk")
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_network_security_group")
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_availability_set")
    cross_scan_registry.register_dependency("azure_virtual_machine", "azure_image")
    
    # Managed Disks
    register_resource_scanner(
        resource_type="azure_managed_disk",
        scanner_function="terraback.cli.azure.compute.disks:scan_azure_disks",
        priority=16
    )
    cross_scan_registry.register_dependency("azure_managed_disk", "azure_virtual_machine")
    cross_scan_registry.register_dependency("azure_managed_disk", "azure_snapshot")
    
    # VM Scale Sets
    from terraback.core.license import Tier
    register_resource_scanner(
        resource_type="azure_vmss",
        scanner_function="terraback.cli.azure.compute.vmss:scan_vm_scale_sets",
        priority=25,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_vmss", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_vmss", "azure_virtual_network")
    cross_scan_registry.register_dependency("azure_vmss", "azure_subnet")
    cross_scan_registry.register_dependency("azure_vmss", "azure_load_balancer")
    
    # SSH Keys
    register_resource_scanner(
        resource_type="azure_ssh_key",
        scanner_function="terraback.cli.azure.compute.ssh_keys:scan_ssh_keys",
        priority=5
    )
    cross_scan_registry.register_dependency("azure_ssh_key", "azure_resource_group")
    
    # Function Apps
    register_resource_scanner(
        resource_type="azure_function_app",
        scanner_function="terraback.cli.azure.compute.function_apps:scan_function_apps",
        priority=30,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_function_app", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_function_app", "azure_app_service_plan")
    cross_scan_registry.register_dependency("azure_function_app", "azure_storage_account")
    
    # App Service Plans
    register_resource_scanner(
        resource_type="azure_app_service_plan",
        scanner_function="terraback.cli.azure.compute.app_services:scan_app_service_plans",
        priority=25,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_app_service_plan", "azure_resource_group")
    
    # Web Apps
    register_resource_scanner(
        resource_type="azure_web_app",
        scanner_function="terraback.cli.azure.compute.app_services:scan_web_apps",
        priority=30,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_web_app", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_web_app", "azure_app_service_plan")
    
    # Note: SQL resources moved to database module, Key Vault moved to security module, 
    # Container resources moved to container module

# Add sub-commands
app.add_typer(virtual_machines.app, name="vm")
app.add_typer(disks.app, name="disk")
app.add_typer(ssh_keys.app, name="ssh-key")

# Import vmss_cli separately to avoid circular import
from .vmss_cli import app as vmss_app
app.add_typer(vmss_app, name="vmss")

# Add convenience command for scanning all compute resources
@app.command("scan-all")
def scan_all_compute(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies")
):
    """Scan all Azure compute resources."""
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
            "azure_virtual_machine",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        # Scan VMs
        virtual_machines.scan_vms(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name,
            include_all_states=True
        )
        
        # Scan Disks
        disks.scan_disks(
            output_dir=output_dir,
            subscription_id=subscription_id,
            location=location,
            resource_group_name=resource_group_name
        )
        
        # Scan SSH Keys
        ssh_keys.scan_ssh_keys(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )

# ----------------------------------------------------------------------
# Professional tier scan functions (stubs) - append below existing content
# ----------------------------------------------------------------------

def scan_azure_ssh_keys(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure SSH Keys."""
    from .ssh_keys import scan_ssh_keys
    scan_ssh_keys(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )

from terraback.core.license import require_professional

@require_professional
def scan_azure_sql_servers(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure SQL Servers (Professional feature)."""
    from terraback.cli.azure.database.sql_databases import scan_sql_servers
    scan_sql_servers(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_sql_databases(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure SQL Databases (Professional feature)."""
    from terraback.cli.azure.database.sql_databases import scan_sql_databases
    scan_sql_databases(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_app_service_plans(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure App Service Plans (Professional feature)."""
    from .app_services import scan_app_service_plans
    scan_app_service_plans(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_web_apps(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Web Apps (Professional feature)."""
    from .app_services import scan_web_apps
    scan_web_apps(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_function_apps(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Function Apps (Professional feature)."""
    from .function_apps import scan_function_apps
    scan_function_apps(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_key_vaults(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Key Vaults (Professional feature)."""
    from terraback.cli.azure.security.key_vaults import scan_key_vaults
    scan_key_vaults(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


@require_professional
def scan_azure_container_registries(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Container Registries (Professional feature)."""
    from terraback.cli.azure.container.container_registries import scan_container_registries
    scan_container_registries(
        output_dir=output_dir,
        subscription_id=subscription_id
    )


from terraback.core.license import require_professional

@require_professional
def scan_azure_kubernetes_clusters(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan Azure Kubernetes Clusters (Professional feature)."""
    from terraback.cli.azure.container.aks_clusters import scan_aks_clusters
    scan_aks_clusters(
        output_dir=output_dir,
        subscription_id=subscription_id
    )
