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

app = typer.Typer(name="monitor", help="Manage Azure Monitor resources", no_args_is_help=True)


def register():
    """Register monitoring resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register Log Analytics Workspace scanner
    register_resource_scanner(
        resource_type="azure_log_analytics_workspace",
        scanner_function="terraback.cli.azure.monitoring.log_analytics:scan_log_analytics_workspaces",
        priority=60,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Action Group scanner
    register_resource_scanner(
        resource_type="azure_monitor_action_group",
        scanner_function="terraback.cli.azure.monitoring.action_groups:scan_action_groups",
        priority=61,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Metric Alert scanner
    register_resource_scanner(
        resource_type="azure_monitor_metric_alert",
        scanner_function="terraback.cli.azure.monitoring.metric_alerts:scan_metric_alerts",
        priority=62,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Dashboard scanner
    register_resource_scanner(
        resource_type="azure_portal_dashboard",
        scanner_function="terraback.cli.azure.monitoring.dashboards:scan_dashboards",
        priority=63,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-workspaces")
def scan_log_analytics_workspaces(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Log Analytics Workspaces and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Log Analytics Workspaces in subscription '{subscription_id}'...")
    
    from .log_analytics import scan_log_analytics_workspaces as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Log Analytics Workspace(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_log_analytics_workspace', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_log_analytics_workspace', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-action-groups")
def scan_action_groups(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Monitor Action Groups and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Monitor Action Groups in subscription '{subscription_id}'...")
    
    from .action_groups import scan_action_groups as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Action Group(s)")
    
    # Write Terraform files
    for resource in resources:
        write_terraform_file(output_dir, resource, 'azure_monitor_action_group')
    
    # Generate import commands
    if resources:
        import_commands = generate_import_commands(resources, 'azure_monitor_action_group')
        import_manager = ImportManager(output_dir, 'azure_monitor_action_group')
        import_manager.save_import_commands(import_commands)
        typer.echo(f"Import commands saved to: {import_manager.import_file}")


@app.command("scan-alerts")
def scan_metric_alerts(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Monitor Metric Alerts and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Monitor Metric Alerts in subscription '{subscription_id}'...")
    
    from .metric_alerts import scan_metric_alerts as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Metric Alert(s)")
    
    # Write Terraform files
    for resource in resources:
        write_terraform_file(output_dir, resource, 'azure_monitor_metric_alert')
    
    # Generate import commands
    if resources:
        import_commands = generate_import_commands(resources, 'azure_monitor_metric_alert')
        import_manager = ImportManager(output_dir, 'azure_monitor_metric_alert')
        import_manager.save_import_commands(import_commands)
        typer.echo(f"Import commands saved to: {import_manager.import_file}")


@app.command("scan-dashboards")
def scan_dashboards(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Portal Dashboards and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Portal Dashboards in subscription '{subscription_id}'...")
    
    from .dashboards import scan_dashboards as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Dashboard(s)")
    
    # Write Terraform files
    for resource in resources:
        write_terraform_file(output_dir, resource, 'azure_portal_dashboard')
    
    # Generate import commands
    if resources:
        import_commands = generate_import_commands(resources, 'azure_portal_dashboard')
        import_manager = ImportManager(output_dir, 'azure_portal_dashboard')
        import_manager.save_import_commands(import_commands)
        typer.echo(f"Import commands saved to: {import_manager.import_file}")


@app.command("scan-all")
def scan_all_monitoring(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan all monitoring resources."""
    scan_log_analytics_workspaces(output_dir, subscription_id, resource_group_name)
    scan_action_groups(output_dir, subscription_id, resource_group_name)
    scan_metric_alerts(output_dir, subscription_id, resource_group_name)
    scan_dashboards(output_dir, subscription_id, resource_group_name)
