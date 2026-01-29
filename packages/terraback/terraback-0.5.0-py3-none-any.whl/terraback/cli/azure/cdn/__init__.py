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

logger = get_logger(__name__)

app = typer.Typer(name="cdn", help="Manage Azure CDN resources", no_args_is_help=True)


def register():
    """Register CDN resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register CDN Profile scanner
    register_resource_scanner(
        resource_type="azure_cdn_profile",
        scanner_function="terraback.cli.azure.cdn.cdn_profiles:scan_cdn_profiles",
        priority=30,
        tier=Tier.PROFESSIONAL
    )
    
    # Register CDN Endpoint scanner
    register_resource_scanner(
        resource_type="azure_cdn_endpoint",
        scanner_function="terraback.cli.azure.cdn.cdn_endpoints:scan_cdn_endpoints",
        priority=31,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-profiles")
def scan_cdn_profiles(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure CDN Profiles and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning CDN Profiles in subscription '{subscription_id}'...")
    
    from .cdn_profiles import scan_cdn_profiles as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} CDN Profile(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_cdn_profile', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_cdn_profile', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-endpoints")
def scan_cdn_endpoints(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure CDN Endpoints and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning CDN Endpoints in subscription '{subscription_id}'...")
    
    from .cdn_endpoints import scan_cdn_endpoints as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} CDN Endpoint(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_cdn_endpoint', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_cdn_endpoint', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-all")
def scan_all_cdn(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan all CDN resources (profiles and endpoints)."""
    scan_cdn_profiles(output_dir, subscription_id, resource_group_name)
    scan_cdn_endpoints(output_dir, subscription_id, resource_group_name)
