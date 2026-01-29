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

app = typer.Typer(name="vmss", help="Manage Azure VM Scale Sets", no_args_is_help=True)


@app.command("scan")
def scan_vmss(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure VM Scale Sets and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning VM Scale Sets in subscription '{subscription_id}'...")
    
    from .vmss import scan_vm_scale_sets as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by location if specified
    if location:
        resources = [r for r in resources if r.get('location', '').lower() == location.lower()]
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} VM Scale Set(s)")
    
    # Write Terraform files
    for resource in resources:
        write_terraform_file(output_dir, resource, resource['resource_type'])
    
    # Generate import commands
    if resources:
        # Group by resource type
        linux_vmss = [r for r in resources if r['resource_type'] == 'azure_linux_virtual_machine_scale_set']
        windows_vmss = [r for r in resources if r['resource_type'] == 'azure_windows_virtual_machine_scale_set']
        
        if linux_vmss:
            import_commands = generate_import_commands(linux_vmss, 'azure_linux_virtual_machine_scale_set')
            import_manager = ImportManager(output_dir, 'azure_linux_virtual_machine_scale_set')
            import_manager.save_import_commands(import_commands)
            typer.echo(f"Linux VMSS import commands saved to: {import_manager.import_file}")
        
        if windows_vmss:
            import_commands = generate_import_commands(windows_vmss, 'azure_windows_virtual_machine_scale_set')
            import_manager = ImportManager(output_dir, 'azure_windows_virtual_machine_scale_set')
            import_manager.save_import_commands(import_commands)
            typer.echo(f"Windows VMSS import commands saved to: {import_manager.import_file}")


@app.command("list")
def list_vmss(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files")
):
    """List all VM Scale Sets previously scanned."""
    linux_manager = ImportManager(output_dir, "azure_linux_virtual_machine_scale_set")
    windows_manager = ImportManager(output_dir, "azure_windows_virtual_machine_scale_set")
    
    typer.echo("=== Linux VM Scale Sets ===")
    linux_manager.list_all()
    
    typer.echo("\n=== Windows VM Scale Sets ===")
    windows_manager.list_all()


@app.command("import")
def import_vmss(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import files"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be imported without executing"),
    parallel: int = typer.Option(1, "--parallel", help="Number of parallel imports (Professional feature)"),
):
    """Import VM Scale Sets into Terraform state."""
    from terraback.core.license import check_feature_access, Tier
    
    linux_manager = ImportManager(output_dir, "azure_linux_virtual_machine_scale_set")
    windows_manager = ImportManager(output_dir, "azure_windows_virtual_machine_scale_set")
    
    use_parallel = parallel > 1 and check_feature_access(Tier.PROFESSIONAL)
    if parallel > 1 and not use_parallel:
        typer.echo("Parallel import requires Professional license. Using sequential import.")
    
    typer.echo("Importing Linux VM Scale Sets...")
    linux_manager.run_imports(dry_run=dry_run, parallel=use_parallel and parallel or 1)
    
    typer.echo("\nImporting Windows VM Scale Sets...")
    windows_manager.run_imports(dry_run=dry_run, parallel=use_parallel and parallel or 1)
