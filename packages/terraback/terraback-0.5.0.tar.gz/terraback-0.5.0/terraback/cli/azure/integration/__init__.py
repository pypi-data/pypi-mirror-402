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

app = typer.Typer(name="integration", help="Manage Azure integration resources", no_args_is_help=True)


def register():
    """Register integration resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register API Management scanner
    register_resource_scanner(
        resource_type="azure_api_management",
        scanner_function="terraback.cli.azure.integration.api_management:scan_api_management",
        priority=70,
        tier=Tier.PROFESSIONAL
    )
    
    # Register API Management API scanner
    register_resource_scanner(
        resource_type="azure_api_management_api",
        scanner_function="terraback.cli.azure.integration.api_management_apis:scan_api_management_apis",
        priority=71,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-apim")
def scan_api_management(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure API Management instances and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning API Management instances in subscription '{subscription_id}'...")
    
    from .api_management import scan_api_management as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} API Management instance(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_api_management', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_api_management', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-apis")
def scan_api_management_apis(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
    api_management_name: Optional[str] = typer.Option(None, "--apim-name", help="Filter by API Management instance name"),
):
    """Scan Azure API Management APIs and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning API Management APIs in subscription '{subscription_id}'...")
    
    from .api_management_apis import scan_api_management_apis as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    # Filter by API Management instance if specified
    if api_management_name:
        resources = [r for r in resources if r.get('properties', {}).get('api_management_name', '').lower() == api_management_name.lower()]
    
    typer.echo(f"Found {len(resources)} API(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_api_management_api', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_api_management_api', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-all")
def scan_all_integration(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan all integration resources."""
    scan_api_management(output_dir, subscription_id, resource_group_name)
    scan_api_management_apis(output_dir, subscription_id, resource_group_name)
