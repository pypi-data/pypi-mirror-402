"""Azure database services module."""
from terraback.utils.cross_scan_registry import register_resource_scanner

import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="database",
    help="Work with Azure Database resources.",
    no_args_is_help=True
)

def register():
    """Register database resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # SQL Servers
    register_resource_scanner(
        resource_type="azure_sql_server",
        scanner_function="terraback.cli.azure.database.sql_databases:scan_sql_servers",
        priority=20,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_sql_server", "azure_resource_group")
    
    # SQL Databases
    register_resource_scanner(
        resource_type="azure_sql_database",
        scanner_function="terraback.cli.azure.database.sql_databases:scan_sql_databases",
        priority=25,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_sql_database", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_sql_database", "azure_sql_server")
    
    # SQL Elastic Pools
    register_resource_scanner(
        resource_type="azure_sql_elastic_pool",
        scanner_function="terraback.cli.azure.database.sql_databases:scan_sql_elastic_pools",
        priority=22,
        tier=Tier.PROFESSIONAL
    )
    cross_scan_registry.register_dependency("azure_sql_elastic_pool", "azure_resource_group")
    cross_scan_registry.register_dependency("azure_sql_elastic_pool", "azure_sql_server")
    
    # SQL databases can optionally belong to elastic pools
    cross_scan_registry.register_dependency("azure_sql_database", "azure_sql_elastic_pool")

# Import the sql_databases module for CLI commands
from . import sql_databases

# Add SQL CLI commands
if hasattr(sql_databases, 'app'):
    app.add_typer(sql_databases.app, name="sql")

@app.command("scan-all")
def scan_all_database(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
):
    """Scan all Azure Database resources."""
    from terraback.cli.azure.session import get_default_subscription_id
    from .sql_databases import scan_sql_servers, scan_sql_databases, scan_sql_elastic_pools
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning all database resources in subscription '{subscription_id}'...")
    
    # Scan SQL Servers first
    typer.echo("\n=== Scanning SQL Servers ===")
    scan_sql_servers(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )
    
    # Scan SQL Elastic Pools
    typer.echo("\n=== Scanning SQL Elastic Pools ===")
    scan_sql_elastic_pools(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )
    
    # Scan SQL Databases
    typer.echo("\n=== Scanning SQL Databases ===")
    scan_sql_databases(
        output_dir=output_dir,
        subscription_id=subscription_id,
        resource_group_name=resource_group_name
    )
    
    typer.echo("\nDatabase scanning complete!")