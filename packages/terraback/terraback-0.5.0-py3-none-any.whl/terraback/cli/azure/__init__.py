import typer
import json
from pathlib import Path
from typing import Optional

# --- App Definition ---
app = typer.Typer(
    name="azure",
    help="Work with Microsoft Azure resources.",
    no_args_is_help=True,
)

# --- Service Module Imports ---
from . import compute, network, storage, loadbalancer, resources, caching, cdn, dns, messaging, monitoring, integration, security, database, container

# --- Module and Dependency Definitions ---
SERVICE_MODULES = [
    ("Compute", compute),
    ("Network", network),
    ("Storage", storage),
    ("Load Balancer", loadbalancer),
    ("Resources", resources),
    ("Caching", caching),
    ("CDN", cdn),
    ("DNS", dns),
    ("Database", database),
    ("Container", container),
    ("Messaging", messaging),
    ("Monitoring", monitoring),
    ("Integration", integration),
    ("Security", security),
]

PROFESSIONAL_DEPENDENCIES = [
    ("azure_virtual_machine", "azure_resource_group"),
    ("azure_virtual_machine", "azure_virtual_network"),
    ("azure_virtual_machine", "azure_network_interface"),
    ("azure_network_interface", "azure_subnet"),
    ("azure_network_interface", "azure_resource_group"),
    ("azure_subnet", "azure_virtual_network"),
    ("azure_lb", "azure_resource_group"),
    ("azure_storage_account", "azure_resource_group"),
    ("azure_redis_cache", "azure_resource_group"),
    ("azure_redis_cache", "azure_subnet"),
    ("azure_cdn_profile", "azure_resource_group"),
    ("azure_cdn_endpoint", "azure_cdn_profile"),
    ("azure_dns_zone", "azure_resource_group"),
    ("azure_servicebus_namespace", "azure_resource_group"),
    ("azure_servicebus_queue", "azure_servicebus_namespace"),
    ("azure_servicebus_topic", "azure_servicebus_namespace"),
    ("azure_servicebus_subscription", "azure_servicebus_topic"),
    ("azure_log_analytics_workspace", "azure_resource_group"),
    ("azure_monitor_action_group", "azure_resource_group"),
    ("azure_monitor_metric_alert", "azure_resource_group"),
    ("azure_monitor_metric_alert", "azure_monitor_action_group"),
    ("azure_api_management", "azure_resource_group"),
    ("azure_api_management", "azure_virtual_network"),
    ("azure_api_management", "azure_subnet"),
    ("azure_api_management_api", "azure_api_management"),
    ("azure_user_assigned_identity", "azure_resource_group"),
]

# --- Registration Logic ---
_registered = False

def register():
    """
    Register all Azure resources and dependencies with the central cross-scan registry.
    """
    global _registered
    if _registered:
        return
    _registered = True

    from terraback.core.license import check_feature_access, Tier
    from terraback.utils.cross_scan_registry import cross_scan_registry

    with cross_scan_registry.autosave_mode(False):
        for service_name, module in SERVICE_MODULES:
            try:
                if hasattr(module, "register"):
                    module.register()
            except Exception as e:
                typer.echo(f"Warning: Failed to register {service_name}: {e}", err=True)

        if check_feature_access(Tier.PROFESSIONAL):
            for source, target in PROFESSIONAL_DEPENDENCIES:
                cross_scan_registry.register_dependency(source, target)

        cross_scan_registry.flush()

# --- CLI Command Definitions ---

# Add each service's Typer app as a subcommand.
app.add_typer(compute.app, name="compute", help="VMs, disks, and compute resources")
app.add_typer(network.app, name="network", help="VNets, subnets, and network interfaces")
app.add_typer(storage.app, name="storage", help="Storage accounts and related resources")
app.add_typer(loadbalancer.app, name="lb", help="Load balancers")
app.add_typer(resources.app, name="resources", help="Resource groups")
app.add_typer(caching.app, name="caching", help="Redis Cache and caching resources")
app.add_typer(cdn.app, name="cdn", help="CDN profiles and endpoints")
app.add_typer(dns.app, name="dns", help="DNS zones and records")
app.add_typer(database.app, name="database", help="SQL servers, databases, and elastic pools")
app.add_typer(container.app, name="container", help="Container registries and Kubernetes services")
app.add_typer(messaging.app, name="messaging", help="Service Bus and messaging resources")
app.add_typer(monitoring.app, name="monitor", help="Monitor, alerts, and analytics resources")
app.add_typer(integration.app, name="integration", help="API Management and integration resources")
app.add_typer(security.app, name="security", help="Security, RBAC, and identity resources")

@app.command("scan-all")
def scan_all_azure(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies (Professional feature)"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel workers (Professional feature)"),
    check: bool = typer.Option(True, "--check/--skip-check", help="Validate Terraform after scan"),
):
    """Scan all available Azure resources based on your license tier."""
    register()

    from terraback.cli.azure.session import get_default_subscription_id
    from terraback.core.license import check_feature_access, Tier
    # Import the new function here
    from terraback.utils.cross_scan_registry import cross_scan_registry, recursive_scan, get_all_scan_functions
    from terraback.utils.parallel_scan import ParallelScanManager, create_scan_tasks

    # 1. Authenticate with Azure
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Scanning Azure resources in subscription '{subscription_id}'...")
    if location:
        typer.echo(f"Filtering by location: {location}")
    if resource_group_name:
        typer.echo(f"Filtering by resource group: {resource_group_name}")

    # 2. Handle Dependency Scanning (--with-deps)
    if with_deps:
        if check_feature_access(Tier.PROFESSIONAL):
            typer.echo("\nScanning with dependency resolution...")
            recursive_scan("azure_resource_group", output_dir=output_dir, subscription_id=subscription_id, location=location, resource_group_name=resource_group_name)
            typer.echo("\nScan complete!")
            return
        else:
            typer.echo("\nDependency scanning ensures no missing references in your Terraform.")
            typer.echo("Unlock with Professional ($499 lifetime): terraback license activate <key>\n")

    # 3. Perform Standard Scan

    all_scans = get_all_scan_functions() 
    scan_configs = []
    skipped_configs = []

    for name, details in all_scans.items():
        if "azure" in name and check_feature_access(details.get("tier", Tier.COMMUNITY)):
            scan_configs.append({'name': name, 'function': details['function']})
        elif "azure" in name:
            skipped_configs.append(name)
    
    if skipped_configs:
        typer.echo(f"\nNote: {len(skipped_configs)} advanced resources available with Professional license.")

    base_kwargs = {
        'output_dir': output_dir, 'subscription_id': subscription_id,
        'location': location, 'resource_group_name': resource_group_name
    }
    tasks = create_scan_tasks(scan_configs, base_kwargs)

    # 4. Execute Scans
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)

    if use_parallel:
        typer.echo(f"\nScanning {len(tasks)} resource types in parallel with {parallel} workers...")
        manager = ParallelScanManager(max_workers=parallel)
        manager.scan_parallel(tasks)
    else:
        if parallel > 1:
            typer.echo("\nParallel scanning (5x faster) available with Professional license.")
        typer.echo(f"\nScanning {len(tasks)} resource types sequentially...")
        failed_tasks = []
        for task in tasks:
            typer.echo(f"--- Scanning {task.name} ---")
            try:
                task.function(**task.kwargs)
            except Exception as e:
                typer.echo(f"Error scanning {task.name}: {e}", err=True)
                failed_tasks.append((task.name, str(e)))

    # Run post-scan processing to fix cross-resource references
    try:
        from terraback.utils.post_scan_processor import run_post_scan_processing
        if run_post_scan_processing(output_dir):
            typer.echo("Applied cross-resource optimizations")
        else:
            typer.echo("Post-processing encountered issues")
    except Exception as e:
        typer.echo(f"Post-processing failed: {e}")
    
    typer.echo("\nScan complete!")
    typer.echo(f"Results saved to: {output_dir}/")
    
    # Report any failures that occurred during sequential scanning
    if not use_parallel and 'failed_tasks' in locals() and failed_tasks:
        typer.echo(f"\nWarning: {len(failed_tasks)} resource type(s) failed to scan:", err=True)
        for task_name, error in failed_tasks:
            typer.echo(f"  - {task_name}: {error}", err=True)

    if check:
        from terraback.utils.terraform_checker import check_and_fix_terraform_files
        check_and_fix_terraform_files(output_dir)


@app.command("import")
def import_all_azure(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    terraform_dir: Optional[Path] = typer.Option(None, "--terraform-dir", "-t", help="Terraform directory (defaults to output_dir)"),
    method: str = typer.Option(
        "auto",
        "--method",
        "-m",
        help="Import method: 'auto' (detect best), 'bulk' (fastest for Terraform 1.5+), 'sequential' (reliable)",
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Import all scanned Azure resources into Terraform state.
    
    This command supports two import methods:
    
    - bulk: Uses Terraform import blocks (requires Terraform 1.5+), imports all 
            resources in a single operation (~2-3 minutes for hundreds of resources)
            
    - sequential: Imports resources one by one, slower but avoids state lock 
                  conflicts (~4 seconds per resource)
    
    By default, it automatically detects the best method based on your Terraform version.
    """
    from terraback.utils.terraform_import import import_resources
    
    if terraform_dir is None:
        terraform_dir = output_dir
    
    # Load import files from import/ subdirectory
    import_dir = output_dir / "import"
    import_files = list(import_dir.glob("*_import.json")) if import_dir.exists() else []
    all_imports = []
    
    for import_file in import_files:
        try:
            with open(import_file, "r") as f:
                resources = json.load(f)
                for resource in resources:
                    # Ensure all required fields are present
                    resource_type = resource.get("resource_type")
                    resource_name = resource.get("resource_name") 
                    resource_id = resource.get("remote_id")
                    
                    if not all([resource_type, resource_name, resource_id]):
                        typer.echo(f"Warning: Skipping resource with missing fields in {import_file.name}: type={resource_type}, name={resource_name}, id={resource_id}", err=True)
                        continue
                        
                    all_imports.append({
                        "type": resource_type,
                        "name": resource_name,
                        "id": resource_id,
                        "file": import_file.name,
                    })
        except Exception as e:
            typer.echo(f"Error reading {import_file.name}: {e}", err=True)
    
    if not all_imports:
        typer.echo("No resources to import. Run 'terraback azure scan-all' first.")
        raise typer.Exit(1)
    
    # Show summary
    by_type = {}
    for imp in all_imports:
        resource_type = imp["type"]
        by_type[resource_type] = by_type.get(resource_type, 0) + 1
    
    typer.echo(f"\nFound {len(all_imports)} resources to import:")
    for resource_type, count in sorted(by_type.items()):
        typer.echo(f"  {resource_type}: {count}")
    
    # Confirm
    if not yes:
        if not typer.confirm("\nDo you want to proceed with the import?"):
            raise typer.Exit(0)
    
    # Import
    typer.echo(f"\nImporting resources using {method} method...")
    imported, failed, failed_details = import_resources(
        terraform_dir,
        all_imports,
        method=method,
        progress=True,
        skip_confirm=yes  # Pass the yes flag to skip additional confirmations
    )
    
    if failed > 0:
        typer.echo("\nSome resources failed to import:")
        for fail in failed_details[:5]:
            typer.echo(f"  - {fail.get('address', 'unknown')}: {fail.get('error', 'unknown error')}")
        raise typer.Exit(1)
    else:
        typer.echo("\nAll resources imported successfully!")
        typer.echo("Run 'terraform plan' to verify the imported state.")


@app.command("list-resources")
def list_azure_resources(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files")
):
    """List all Azure resources previously scanned."""
    from terraback.utils.importer import ImportManager
    resource_types = [
        "azure_resource_group", "azure_virtual_machine", "azure_managed_disk",
        "azure_virtual_network", "azure_subnet", "azure_network_security_group",
        "azure_network_interface", "azure_storage_account", "azure_lb",
    ]
    for resource_type in resource_types:
        import_file = output_dir / "import" / f"{resource_type}_import.json"
        if import_file.exists():
            typer.echo(f"\n=== {resource_type} ===")
            ImportManager(output_dir, resource_type).list_all()

@app.command("clean")
def clean_azure_files(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory to clean"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation")
):
    """Clean all Azure-related generated files."""
    from terraback.utils.cleanup import clean_generated_files
    if not yes:
        confirm = typer.confirm(f"This will delete all Azure .tf and _import.json files in {output_dir}. Continue?")
        if not confirm:
            raise typer.Abort()
    azure_prefixes = [
        "azure_resource_group", "azure_virtual_machine", "azure_managed_disk",
        "azure_virtual_network", "azure_subnet", "azure_network_security_group",
        "azure_network_interface", "azure_storage_account", "azure_lb",
    ]
    for prefix in azure_prefixes:
        clean_generated_files(output_dir, prefix)
    typer.echo("Azure generated files cleaned successfully!")
