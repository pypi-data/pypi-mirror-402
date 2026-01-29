"""Azure Monitor Dashboards scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import json
from terraback.core.license import require_professional

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="dashboards", help="Scan and import Azure Monitor Dashboards.")


@require_professional
def scan_dashboards(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None  # Accept but ignore location parameter for compatibility
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Monitor Dashboards and generate Terraform configurations.
    
    This function retrieves all Dashboards from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        
    Returns:
        List of Dashboard resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    # Portal dashboard client uses ResourceManagementClient
    resource_client = get_azure_client('ResourceManagementClient', subscription_id)
    dashboards: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure Monitor Dashboards...")
    print("Scanning for Azure Monitor Dashboards...")
    
    # List all dashboards (they are a generic resource type)
    @safe_azure_operation("list dashboards", default_return=[])
    def list_dashboards():
        return list(resource_client.resources.list(
            filter="resourceType eq 'Microsoft.Portal/dashboards'"
        ))
    
    dashboard_list = list_dashboards()
    
    # Process each dashboard
    for dashboard in dashboard_list:
        dashboard_dict = format_resource_dict(dashboard, 'portal_dashboard')
        
        # Get full dashboard details
        @safe_azure_operation(f"get dashboard {dashboard.name}", default_return=None)
        def get_dashboard_details():
            return resource_client.resources.get_by_id(
                resource_id=dashboard.id,
                api_version='2020-09-01-preview'
            )
        
        full_dashboard = get_dashboard_details()
        if full_dashboard and hasattr(full_dashboard, 'properties'):
            _format_dashboard_properties(dashboard_dict, full_dashboard)
        
        dashboards.append(dashboard_dict)
        logger.debug(f"Processed dashboard: {dashboard.name}")    # Process resources before generation
    dashboards = process_resources(dashboards, "azure_portal_dashboard")
    

    
    # Generate Terraform files
    if dashboards:
        generate_tf_auto(dashboards, "azure_portal_dashboard", output_dir)
        
        generate_imports_file(
            "azure_portal_dashboard",
            dashboards,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No Dashboards found.")
        logger.info("No Dashboards found.")
    
    return dashboards


def _format_dashboard_properties(dashboard_dict: Dict[str, Any], dashboard: Any) -> None:
    """Format dashboard properties."""
    if not hasattr(dashboard, 'properties'):
        return
    
    props = dashboard.properties
    
    # Dashboard properties
    if hasattr(props, 'lenses'):
        dashboard_dict['dashboard_properties'] = {
            'lenses': []
        }
        
        for lens in props.lenses:
            lens_dict = {
                'order': lens.order if hasattr(lens, 'order') else 0,
                'parts': []
            }
            
            if hasattr(lens, 'parts'):
                for part in lens.parts:
                    part_dict = {
                        'position': {
                            'x': part.position.x if hasattr(part.position, 'x') else 0,
                            'y': part.position.y if hasattr(part.position, 'y') else 0,
                            'row_span': part.position.row_span if hasattr(part.position, 'row_span') else 1,
                            'col_span': part.position.col_span if hasattr(part.position, 'col_span') else 1
                        }
                    }
                    
                    if hasattr(part, 'metadata'):
                        # Convert metadata to JSON string for Terraform
                        try:
                            part_dict['metadata'] = json.dumps(part.metadata)
                        except Exception:
                            part_dict['metadata'] = '{}'
                    
                    lens_dict['parts'].append(part_dict)
            
            dashboard_dict['dashboard_properties']['lenses'].append(lens_dict)
    
    # Metadata
    if hasattr(props, 'metadata'):
        try:
            dashboard_dict['metadata'] = json.dumps(props.metadata)
        except Exception:
            dashboard_dict['metadata'] = '{}'


@app.command("scan")
def scan_dashboards_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID.")
):
    """Scans Azure Monitor Dashboards and generates Terraform code."""
    typer.echo(f"Scanning for Azure Monitor Dashboards in subscription '{subscription_id}'...")
    
    try:
        scan_dashboards(output_dir=output_dir, subscription_id=subscription_id)
    except Exception as e:
        typer.echo(f"Error scanning Dashboards: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_dashboards(
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Lists all Dashboard resources previously generated."""
    ImportManager(output_dir, "azure_portal_dashboard").list_all()


@app.command("import")
def import_dashboard(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Dashboard to import."),
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Runs terraform import for a specific Dashboard."""
    ImportManager(output_dir, "azure_portal_dashboard").find_and_import(resource_id)