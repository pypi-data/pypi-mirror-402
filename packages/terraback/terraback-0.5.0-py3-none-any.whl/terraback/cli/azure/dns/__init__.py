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

app = typer.Typer(name="dns", help="Manage Azure DNS resources", no_args_is_help=True)


def register():
    """Register DNS resources with the cross-scan registry."""
    from terraback.utils.cross_scan_registry import cross_scan_registry
    from terraback.core.license import Tier
    
    # Register DNS Zone scanner
    register_resource_scanner(
        resource_type="azure_dns_zone",
        scanner_function="terraback.cli.azure.dns.dns_zones:scan_dns_zones",
        priority=40,
        tier=Tier.PROFESSIONAL
    )
    
    # Register DNS Record scanner
    register_resource_scanner(
        resource_type="azure_dns_record",
        scanner_function="terraback.cli.azure.dns.dns_records:scan_dns_records",
        priority=41,
        tier=Tier.PROFESSIONAL
    )


@app.command("scan-zones")
def scan_dns_zones(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan Azure DNS Zones and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning DNS Zones in subscription '{subscription_id}'...")
    
    from .dns_zones import scan_dns_zones as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    typer.echo(f"Found {len(resources)} DNS Zone(s)")
    
    # Write Terraform files
    if resources:
        resources = process_resources(resources, 'azure_dns_zone')
        generate_tf_auto(resources, 'azure_dns_zone', output_dir, provider='azure')

        # Generate import commands
        generate_imports_file('azure_dns_zone', resources,
                            remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-records")
def scan_dns_records(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
    zone_name: Optional[str] = typer.Option(None, "--zone", "-z", help="Filter by DNS zone name"),
):
    """Scan Azure DNS Records and generate Terraform configurations."""
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    if not subscription_id:
        typer.echo("Error: No Azure subscription found. Run 'az login' or set AZURE_SUBSCRIPTION_ID.", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning DNS Records in subscription '{subscription_id}'...")
    
    from .dns_records import scan_dns_records as do_scan
    
    credentials = DefaultAzureCredential()
    resources = do_scan(credentials, subscription_id)
    
    # Filter by resource group if specified
    if resource_group_name:
        resources = [r for r in resources if r.get('resource_group_name', '').lower() == resource_group_name.lower()]
    
    # Filter by zone name if specified
    if zone_name:
        resources = [r for r in resources if r.get('properties', {}).get('zone_name', '').lower() == zone_name.lower()]
    
    typer.echo(f"Found {len(resources)} DNS Record(s)")
    
    # Write Terraform files - group by record type
    record_types = {}
    for resource in resources:
        record_type = resource['properties']['record_type']
        if record_type not in record_types:
            record_types[record_type] = []
        record_types[record_type].append(resource)
    
    for record_type, type_resources in record_types.items():
        resource_type = f"azure_dns_{record_type.lower()}_record"
        if type_resources:
            type_resources = process_resources(type_resources, resource_type)
            generate_tf_auto(type_resources, resource_type, output_dir, provider='azure')

            # Generate import commands
            generate_imports_file(resource_type, type_resources,
                                remote_resource_id_key='id', output_dir=output_dir, provider="azure")


@app.command("scan-all")
def scan_all_dns(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Output directory for Terraform files"),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by resource group"),
):
    """Scan all DNS resources (zones and records)."""
    scan_dns_zones(output_dir, subscription_id, resource_group_name)
    scan_dns_records(output_dir, subscription_id, resource_group_name)
