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

app = typer.Typer(name="security", help="Manage Azure security and identity resources", no_args_is_help=True)


def register():
    """Register security resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Key Vaults
    register_resource_scanner(
        resource_type="azure_key_vault",
        scanner_function="terraback.cli.azure.security.key_vaults:scan_key_vaults",
        priority=15,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_key_vault", "azure_resource_group")
    
    # Register User Assigned Identity scanner
    register_resource_scanner(
        resource_type="azure_user_assigned_identity",
        scanner_function="terraback.cli.azure.security.managed_identities:scan_user_assigned_identities",
        priority=80
    )
    
    # Register Role Assignment scanner
    register_resource_scanner(
        resource_type="azure_role_assignment",
        scanner_function="terraback.cli.azure.security.role_assignments:scan_role_assignments",
        priority=81
    )
    
    # Register Role Definition scanner
    register_resource_scanner(
        resource_type="azure_role_definition",
        scanner_function="terraback.cli.azure.security.role_definitions:scan_role_definitions",
        priority=82
    )


@app.command("scan-identities")
def scan_managed_identities(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure User Assigned Identities and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning User Assigned Identities in subscription '{subscription_id}'...")
    
    from .managed_identities import scan_user_assigned_identities as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} User Assigned Identity(ies)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_user_assigned_identity', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_user_assigned_identity', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-role-assignments")
def scan_role_assignments(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    scope: Optional[str] = typer.Option(None, "--scope", help="Filter by scope (resource ID)"),
):
    """Scan Azure Role Assignments and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Role Assignments in subscription '{subscription_id}'...")
    
    from .role_assignments import scan_role_assignments as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by scope if specified
    if scope:
        resources = [r for r in resources if r.get('properties', {}).get('scope', '').startswith(scope)]
    
    typer.echo(f"Found {len(resources)} Role Assignment(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_role_assignment', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_role_assignment', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-role-definitions")
def scan_role_definitions(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    custom_only: bool = typer.Option(True, "--custom-only/--all", help="Only scan custom role definitions"),
):
    """Scan Azure Role Definitions and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Role Definitions in subscription '{subscription_id}'...")
    if custom_only:
        typer.echo("(Filtering to custom roles only)")
    
    from .role_definitions import scan_role_definitions as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id, custom_only=custom_only)
    
    typer.echo(f"Found {len(resources)} Role Definition(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_role_definition', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_role_definition', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-all")
def scan_all_security(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
):
    """Scan all security and identity resources."""
    scan_managed_identities(output_dir, subscription_id)
    scan_role_assignments(output_dir, subscription_id)
    scan_role_definitions(output_dir, subscription_id)
