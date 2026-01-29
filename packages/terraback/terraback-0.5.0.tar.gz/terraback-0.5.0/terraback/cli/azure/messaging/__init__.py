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

app = typer.Typer(name="messaging", help="Manage Azure messaging resources", no_args_is_help=True)


def register():
    """Register messaging resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register Service Bus Namespace scanner
    register_resource_scanner(
        resource_type="azure_servicebus_namespace",
        scanner_function="terraback.cli.azure.messaging.servicebus:scan_servicebus_namespaces",
        priority=50,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Service Bus Queue scanner
    register_resource_scanner(
        resource_type="azure_servicebus_queue",
        scanner_function="terraback.cli.azure.messaging.servicebus_queues:scan_servicebus_queues",
        priority=51,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Service Bus Topic scanner
    register_resource_scanner(
        resource_type="azure_servicebus_topic",
        scanner_function="terraback.cli.azure.messaging.servicebus_topics:scan_servicebus_topics",
        priority=52,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Service Bus Subscription scanner
    register_resource_scanner(
        resource_type="azure_servicebus_subscription",
        scanner_function="terraback.cli.azure.messaging.servicebus_subscriptions:scan_servicebus_subscriptions",
        priority=53,
        tier=Tier.PROFESSIONAL
    )
    
    # Register Event Hub Namespace scanner
    register_resource_scanner(
        resource_type="azure_eventhub_namespace",
        scanner_function="terraback.cli.azure.messaging.event_hubs:scan_event_hubs",
        priority=54,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-namespaces")
def scan_servicebus_namespaces(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Service Bus Namespaces and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Service Bus Namespaces in subscription '{subscription_id}'...")
    
    from .servicebus import scan_servicebus_namespaces as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Service Bus Namespace(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_servicebus_namespace', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_servicebus_namespace', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-queues")
def scan_servicebus_queues(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Service Bus Queues and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Service Bus Queues in subscription '{subscription_id}'...")
    
    from .servicebus_queues import scan_servicebus_queues as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Service Bus Queue(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_servicebus_queue', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_servicebus_queue', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-event-hubs")
def scan_event_hubs(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure Event Hubs and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning Event Hubs in subscription '{subscription_id}'...")
    
    from .event_hubs import scan_event_hubs as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} Event Hub Namespace(s)")
    
    # Write Terraform files
    if resources:
        generate_tf_auto(resources, 'azure_eventhub_namespace', output_dir, provider='azure')
        
        # Generate import commands
        generate_imports_file('azure_eventhub_namespace', resources, 
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-all")
def scan_all_messaging(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan all messaging resources."""
    scan_servicebus_namespaces(output_dir, subscription_id, resource_group_name)
    scan_servicebus_queues(output_dir, subscription_id, resource_group_name)
    scan_event_hubs(output_dir, subscription_id, resource_group_name)
