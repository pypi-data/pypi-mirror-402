import typer
from terraback.utils.cross_scan_registry import register_resource_scanner
from pathlib import Path
from typing import Optional
from azure.identity import DefaultAzureCredential
from terraback.utils.logging import get_logger
from terraback.cli.azure.session import get_default_subscription_id
from terraback.utils.importer import ImportManager
from terraback.terraform_generator.imports import generate_imports_file
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.cli.azure.resource_processor import process_resources

logger = get_logger(__name__)

app = typer.Typer(name="caching", help="Manage Azure caching resources", no_args_is_help=True)


def register():
    """Register caching resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register Redis Cache scanner
    register_resource_scanner(
        resource_type="azure_redis_cache",
        scanner_function="terraback.cli.azure.caching.redis_caches:scan_redis_caches",
        priority=30,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-redis")
def scan_redis_caches(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Redis Caches and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Redis Caches in subscription '{subscription_id}'...")
    
    from .redis_caches import scan_redis_caches as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by location if specified
    if location:
        resources = [r for r in resources if r.get('location', '').lower() == location.lower()]
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Redis Cache(s)")
    
    # Write Terraform files
    if resources:
        resources = process_resources(resources, 'azure_redis_cache')
        generate_tf_auto(resources, 'azure_redis_cache', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_redis_cache', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("list-redis")
def list_redis_caches(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files")
):
    """List all Redis Caches previously scanned."""
    import_manager = ImportManager(output_dir, "azure_redis_cache")
    import_manager.list_all()


@app.command("import-redis")
def import_redis_caches(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be imported without executing"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel imports (Professional feature)"),
):
    """Import Redis Caches into Terraform state."""
    from terraback.core.license import check_feature_access, Tier
    
    import_manager = ImportManager(output_dir, "azure_redis_cache")
    
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)
    if parallel > 1 and not use_parallel:
        typer.echo("Parallel import requires Professional license. Using sequential import.")
    
    import_manager.run_imports(dry_run=dry_run, parallel=use_parallel and parallel or 1)
