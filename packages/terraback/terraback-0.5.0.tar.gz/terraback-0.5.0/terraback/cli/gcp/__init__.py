import typer
from pathlib import Path
from typing import Optional

# --- App Definition ---
app = typer.Typer(
    name="gcp",
    help="Work with Google Cloud Platform resources.",
    no_args_is_help=True,
)

# --- Service Module Imports ---
# Each of these should have their own Typer app and a `register()` function.
from . import compute, network, storage, loadbalancer, sql, pubsub, secrets, gke, iam, monitoring, dns, cdn, certificate_manager, functions, container_registry, cloud_run, caching, messaging, security, database, integration

# --- Module and Dependency Definitions ---
SERVICE_MODULES = [
    ("Compute", compute),
    ("Network", network),
    ("Storage", storage),
    ("Load Balancer", loadbalancer),
    ("SQL", sql),
    ("PubSub", pubsub),
    ("Secrets", secrets),
    ("GKE", gke),
    ("IAM", iam),
    ("Monitoring", monitoring),
    ("DNS", dns),
    ("CDN", cdn),
    ("Certificate Manager", certificate_manager),
    ("Functions", functions),
    ("Container Registry", container_registry),
    ("Cloud Run", cloud_run),
    ("Caching", caching),
    ("Messaging", messaging),
    ("Security", security),
    ("Database", database),
    ("Integration", integration),
]

PROFESSIONAL_DEPENDENCIES = [
    ("gcp_instance", "gcp_network"),
    ("gcp_instance", "gcp_subnet"),
    ("gcp_instance", "gcp_disk"),
    ("gcp_instance", "gcp_firewall"),
    ("gcp_instance", "gcp_service_account"),
    ("gcp_disk", "gcp_snapshot"),
    ("gcp_disk", "gcp_image"),
    ("gcp_subnet", "gcp_network"),
    ("gcp_firewall", "gcp_network"),
    ("gcp_router", "gcp_network"),
    ("gcp_vpn_gateway", "gcp_network"),
    ("gcp_backend_service", "gcp_instance_group"),
    ("gcp_backend_service", "gcp_health_check"),
    ("gcp_url_map", "gcp_backend_service"),
    ("gcp_target_https_proxy", "gcp_url_map"),
    ("gcp_global_forwarding_rule", "gcp_target_https_proxy"),
    ("gcp_instance_group", "gcp_instance_template"),
    ("gcp_instance_template", "gcp_network"),
    ("gcp_instance_template", "gcp_subnet"),
    ("gcp_bucket", "gcp_bucket_iam_binding"),
    # New professional dependencies
    ("gcp_memorystore_redis", "gcp_network"),
    ("gcp_memorystore_redis", "gcp_subnet"),
    ("gcp_memorystore_memcached", "gcp_network"),
    ("gcp_memorystore_memcached", "gcp_subnet"),
    ("gcp_cloud_tasks_queue", "gcp_service_account"),
    ("gcp_kms_crypto_key", "gcp_kms_key_ring"),
    ("gcp_certificate_authority", "gcp_kms_crypto_key"),
    ("gcp_binary_authorization_policy", "gcp_container_registry"),
    # Database dependencies
    ("gcp_bigtable_instance", "gcp_kms_crypto_key"),
    ("gcp_spanner_instance", "gcp_kms_crypto_key"),
    ("gcp_firestore_database", "gcp_service_account"),
    ("gcp_bigtable_instance", "gcp_service_account"),
    ("gcp_spanner_instance", "gcp_service_account"),
    # Integration dependencies
    ("gcp_api_gateway", "gcp_service_account"),
    ("gcp_workflows", "gcp_service_account"),
    ("gcp_eventarc_trigger", "gcp_pubsub_topic"),
    ("gcp_eventarc_trigger", "gcp_service_account"),
    ("gcp_eventarc_trigger", "gcp_cloud_run_service"),
    ("gcp_eventarc_trigger", "gcp_cloud_function"),
    # New networking dependencies
    ("gcp_nat_gateway", "gcp_router"),
    ("gcp_router", "gcp_network"),
    # Storage dependencies
    ("gcp_filestore", "gcp_network"),
]

# --- Registration Logic ---
_registered = False

def register():
    """
    Register all GCP resources and dependencies with the central cross-scan registry.
    This function is idempotent and will only run once.
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
for service_name_lower, module in [(name.lower().replace(" ", ""), mod) for name, mod in SERVICE_MODULES]:
    if hasattr(module, "app"):
        app.add_typer(module.app, name=service_name_lower, help=f"Work with {service_name_lower.upper()} resources.")

@app.command("scan-all")
def scan_all_gcp(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated files"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="GCP region"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z", help="GCP zone"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Recursively scan dependencies (Professional feature)"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel workers (Professional feature)"),
    check: bool = typer.Option(True, "--check/--skip-check", help="Validate Terraform after scan"),
):
    """
    Scan all available GCP resources based on your license tier.
    """
    register()

    from terraback.core.license import check_feature_access, Tier
    from terraback.core.license import get_active_tier
    from terraback.utils.cross_scan_registry import cross_scan_registry, recursive_scan, get_all_scan_functions
    from terraback.utils.parallel_scan import ParallelScanManager, create_scan_tasks

    # Project ID resolution
    if not project_id:
        from terraback.cli.gcp.session import get_default_project_id
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found. Set GOOGLE_CLOUD_PROJECT or use --project-id", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Scanning GCP resources in project '{project_id}'...")
    if region:
        typer.echo(f"Region: {region}")
    if zone:
        typer.echo(f"Zone: {zone}")

    # 1. Handle Dependency Scanning (--with-deps)
    if with_deps:
        if check_feature_access(Tier.PROFESSIONAL):
            typer.echo("\nScanning with dependency resolution...")
            recursive_scan(
                "gcp_instance",  # or whatever root resource makes sense
                output_dir=output_dir,
                project_id=project_id,
                region=region,
                zone=zone,
            )
            typer.echo("\nScan complete!")
            return
        else:
            typer.echo("\nDependency scanning ensures no missing references in your Terraform.")
            typer.echo("Unlock with Professional ($499 lifetime): terraback license activate <key>\n")

    # 2. Standard Scan (no dependency recursion)
    all_scans = get_all_scan_functions()
    scan_configs = []
    skipped_configs = []

    tier = get_active_tier()

    for name, details in all_scans.items():
        # Only run GCP resources
        if "gcp" in name and check_feature_access(details.get("tier", Tier.COMMUNITY)):
            scan_configs.append({'name': name, 'function': details['function']})
        elif "gcp" in name:
            skipped_configs.append(name)

    if skipped_configs:
        typer.echo(f"\nNote: {len(skipped_configs)} advanced resources available with Professional license.")

    base_kwargs = {
        'output_dir': output_dir, 'project_id': project_id,
        'region': region, 'zone': zone
    }
    tasks = create_scan_tasks(scan_configs, base_kwargs)

    # 3. Execute Scans (Parallel or Sequential)
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)
    if use_parallel:
        typer.echo(f"\nScanning {len(tasks)} resource types in parallel with {parallel} workers...")
        manager = ParallelScanManager(max_workers=parallel)
        manager.scan_parallel(tasks)
    else:
        if parallel > 1:
            typer.echo("\nParallel scanning (5x faster) available with Professional license.")
        typer.echo(f"\nScanning {len(tasks)} resource types sequentially...")
        for task in tasks:
            typer.echo(f"--- Scanning {task.name} ---")
            task.function(**task.kwargs)

    typer.echo("\nScan complete!")
    typer.echo(f"Results saved to: {output_dir}/")

    if check:
        from terraback.utils.terraform_checker import check_and_fix_terraform_files
        check_and_fix_terraform_files(output_dir)


@app.command("import")
def import_all_gcp(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    terraform_dir: Optional[Path] = typer.Option(None, "--terraform-dir", "-t", help="Terraform directory (defaults to output_dir)"),
    method: str = typer.Option(
        "auto",
        "--method",
        "-m",
        help="Import method: 'auto' (detect best), 'bulk' (fastest for Terraform 1.5+), 'sequential' (reliable)",
    ),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Import all scanned GCP resources into Terraform state.
    
    This command supports two import methods:
    
    - bulk: Uses Terraform import blocks (requires Terraform 1.5+), imports all 
            resources in a single operation (~2-3 minutes for hundreds of resources)
            
    - sequential: Imports resources one by one, slower but avoids state lock 
                  conflicts (~4 seconds per resource)
    
    By default, it automatically detects the best method based on your Terraform version.
    """
    import json
    from terraback.utils.terraform_import import import_resources
    
    if terraform_dir is None:
        terraform_dir = output_dir
    
    # Project ID resolution
    if not project_id:
        from terraback.cli.gcp.session import get_default_project_id
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found. Set GOOGLE_CLOUD_PROJECT or use --project-id", err=True)
        raise typer.Exit(code=1)
    
    # Ensure provider configuration is set up correctly
    from terraback.terraform_generator.writer import generate_provider_config
    generate_provider_config(terraform_dir, provider='gcp', project_id=project_id, force_update=True)
    
    # Load import files from import/ subdirectory
    import_dir = output_dir / "import"
    import_files = list(import_dir.glob("*_import.json")) if import_dir.exists() else []
    all_imports = []
    
    for import_file in import_files:
        try:
            with open(import_file, "r") as f:
                resources = json.load(f)
                for resource in resources:
                    all_imports.append({
                        "type": resource.get("resource_type"),
                        "name": resource.get("resource_name"),
                        "id": resource.get("remote_id"),
                        "file": import_file.name,
                    })
        except Exception as e:
            typer.echo(f"Error reading {import_file.name}: {e}", err=True)
    
    if not all_imports:
        typer.echo("No resources to import. Run 'terraback gcp scan-all' first.")
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
        progress=True
    )
    
    if failed > 0:
        typer.echo(f"\n{failed} resources failed to import:")
        if failed_details:
            for fail in failed_details[:10]:  # Show more failed resources
                address = fail.get('address', 'unknown')
                error = fail.get('error', 'unknown error')
                typer.echo(f"  - {address}: {error}")
            if len(failed_details) > 10:
                typer.echo(f"  ... and {len(failed_details) - 10} more failures")
        else:
            typer.echo("  (Error details not available - check Terraform output above)")
        
        typer.echo(f"\nSuccessfully imported: {imported}")
        typer.echo(f"Failed to import: {failed}")
        raise typer.Exit(1)
    else:
        typer.echo("\nAll resources imported successfully!")
        typer.echo("Run 'terraform plan' to verify the imported state.")
