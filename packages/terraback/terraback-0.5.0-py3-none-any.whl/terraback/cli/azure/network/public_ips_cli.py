import typer
from pathlib import Path
from typing import Optional
from azure.identity import DefaultAzureCredential
from terraback.utils.logging import get_logger
from terraback.cli.azure.session import get_default_subscription_id
from terraback.utils.importer import ImportManager
from terraback.terraform_generator.imports import generate_imports_file
from terraback.terraform_generator.writer import generate_tf_auto

logger = get_logger(__name__)

app = typer.Typer(name="public-ip", help="Manage Azure Public IPs", no_args_is_help=True)


@app.command("scan")
def scan_public_ips_cmd(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Public IPs and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Public IPs in subscription '{subscription_id}'...")
    
    from .public_ips import scan_public_ips as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by location if specified
    if location:
        resources = [r for r in resources if r.get('location', '').lower() == location.lower()]
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Public IP(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_public_ip', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_public_ip', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("list")
def list_public_ips(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files")
):
    """List all Public IPs previously scanned."""
    import_manager = ImportManager(output_dir, "azure_public_ip")
    import_manager.list_all()


@app.command("import")
def import_public_ips(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be imported without executing"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel imports (Professional feature)"),
):
    """Import Public IPs into Terraform state."""
    from terraback.core.license import check_feature_access, Tier
    
    import_manager = ImportManager(output_dir, "azure_public_ip")
    
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)
    if parallel > 1 and not use_parallel:
        typer.echo("Parallel import requires Professional license. Using sequential import.")
    
    import_manager.run_imports(dry_run=dry_run, parallel=use_parallel and parallel or 1)
