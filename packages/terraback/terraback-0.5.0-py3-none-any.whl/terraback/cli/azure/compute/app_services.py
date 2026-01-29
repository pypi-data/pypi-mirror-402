"""Azure App Services scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="app-service", help="Scan and import Azure App Services.")

def scan_app_service_plans(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure App Service Plans and generate Terraform configurations.
    
    This function retrieves all App Service Plans from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of App Service Plan resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    web_client = get_azure_client('WebSiteManagementClient', subscription_id)
    app_service_plans: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure App Service Plans...")
    print("Scanning for App Service Plans...")
    
    # List all app service plans with error handling
    @safe_azure_operation("list app service plans", default_return=[])
    def list_plans():
        if resource_group_name:
            return list(web_client.app_service_plans.list_by_resource_group(resource_group_name))
        else:
            return list(web_client.app_service_plans.list())
    
    plan_list = list_plans()
    
    # Process each plan
    for plan in plan_list:
        plan_dict = format_resource_dict(plan, 'app_service_plan')
        
        # Fix Azure API casing issue: Azure returns /serverfarms/ but Terraform expects /serverFarms/
        if 'id' in plan_dict and plan_dict['id']:
            plan_dict['id'] = plan_dict['id'].replace('/serverfarms/', '/serverFarms/')
        
        # Format SKU information
        if hasattr(plan, 'sku') and plan.sku:
            plan_dict['sku_formatted'] = {
                'tier': plan.sku.tier,
                'size': plan.sku.size,
                'capacity': plan.sku.capacity
            }
        
        # Determine OS type from kind
        plan_dict['os_type'] = 'Linux' if plan.kind and 'linux' in plan.kind.lower() else 'Windows'
        
        # Get additional properties
        _get_plan_properties(plan_dict, plan)
        
        app_service_plans.append(plan_dict)
        logger.debug(f"Processed app service plan: {plan.name}")
    
    # Process resources before generation
    app_service_plans = process_resources(app_service_plans, "azure_app_service_plan")
    
    # Generate Terraform files
    if app_service_plans:
        generate_tf_auto(app_service_plans, "azure_app_service_plan", output_dir)
        
        generate_imports_file(
            "azure_app_service_plan",
            app_service_plans,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No App Service Plans found.")
        logger.info("No App Service Plans found.")
    
    return app_service_plans

def _get_plan_properties(plan_dict: Dict[str, Any], plan: Any) -> None:
    """Extract additional properties from App Service Plan."""
    # Add reserved property for Linux plans
    if hasattr(plan, 'reserved'):
        plan_dict['reserved'] = plan.reserved
    
    # Add per-site scaling
    if hasattr(plan, 'per_site_scaling'):
        plan_dict['per_site_scaling'] = plan.per_site_scaling
    
    # Add maximum elastic worker count
    if hasattr(plan, 'maximum_elastic_worker_count'):
        plan_dict['maximum_elastic_worker_count'] = plan.maximum_elastic_worker_count

    # Add hosting environment profile
    if getattr(plan, "hosting_environment_profile", None):
        plan_dict["hosting_environment_profile"] = {
            "id": plan.hosting_environment_profile.id
        }


def scan_web_apps(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Web Apps and generate Terraform configurations.
    
    This function retrieves all Web Apps from the specified subscription,
    excluding Function Apps, and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of Web App resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    web_client = get_azure_client('WebSiteManagementClient', subscription_id)
    web_apps: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure Web Apps...")
    print("Scanning for Web Apps...")
    
    # List all web apps with error handling
    @safe_azure_operation("list web apps", default_return=[])
    def list_apps():
        if resource_group_name:
            return list(web_client.web_apps.list_by_resource_group(resource_group_name))
        else:
            return list(web_client.web_apps.list())
    
    web_apps_list = list_apps()
    
    # Process each web app
    for app in web_apps_list:
        # Skip function apps
        if app.kind and 'functionapp' in app.kind.lower():
            continue
            
        app_dict = format_resource_dict(app, 'web_app')
        
        # Get configuration with error handling
        config = _get_app_configuration(web_client, app_dict, app.name)
        if config:
            app_dict['site_config'] = config.as_dict()
            _process_app_settings(app_dict, config)
            _process_connection_strings(app_dict, config)
        
        # Get authentication settings
        auth_settings = _get_auth_settings(web_client, app_dict, app.name)
        if auth_settings:
            app_dict['auth_settings'] = auth_settings.as_dict()
        
        # Get backup configuration
        backup_config = _get_backup_configuration(web_client, app_dict, app.name)
        if backup_config:
            app_dict['backup'] = backup_config.as_dict()
        
        # Get deployment slots
        slots = _get_deployment_slots(web_client, app_dict, app.name)
        if slots:
            app_dict['deployment_slots'] = slots
        
        web_apps.append(app_dict)
        logger.debug(f"Processed web app: {app.name}")
    
    # Process resources before generation
    web_apps = process_resources(web_apps, "azure_web_app")
    
    # Generate Terraform files
    if web_apps:
        generate_tf_auto(web_apps, "azure_web_app", output_dir)
        
        generate_imports_file(
            "azure_web_app",
            web_apps,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No Web Apps found.")
        logger.info("No Web Apps found.")
    
    return web_apps

def _get_app_configuration(
    web_client: Any,
    app_dict: Dict[str, Any],
    app_name: str
) -> Optional[Any]:
    """Get Web App configuration with error handling."""
    @safe_azure_operation(f"get configuration for {app_name}", default_return=None)
    def get_config():
        return web_client.web_apps.get_configuration(
            resource_group_name=app_dict['resource_group_name'],
            name=app_name
        )
    
    return get_config()


def _process_app_settings(app_dict: Dict[str, Any], config: Any) -> None:
    """Process and format app settings from configuration."""
    if hasattr(config, 'app_settings') and config.app_settings:
        app_dict['app_settings_formatted'] = {
            setting.name: setting.value
            for setting in config.app_settings
            if not setting.name.startswith('WEBSITE_')  # Exclude system settings
        }


def _process_connection_strings(app_dict: Dict[str, Any], config: Any) -> None:
    """Process and format connection strings from configuration."""
    if hasattr(config, 'connection_strings') and config.connection_strings:
        app_dict['connection_strings_formatted'] = [
            {
                'name': cs.name,
                'type': cs.type,
                'value': cs.connection_string
            }
            for cs in config.connection_strings
        ]


def _get_auth_settings(
    web_client: Any,
    app_dict: Dict[str, Any],
    app_name: str
) -> Optional[Any]:
    """Get authentication settings with error handling."""
    @safe_azure_operation(f"get auth settings for {app_name}", default_return=None)
    def get_auth():
        return web_client.web_apps.get_auth_settings(
            resource_group_name=app_dict['resource_group_name'],
            name=app_name
        )
    
    return get_auth()


def _get_backup_configuration(
    web_client: Any,
    app_dict: Dict[str, Any],
    app_name: str
) -> Optional[Any]:
    """Get backup configuration with error handling."""
    @safe_azure_operation(f"get backup config for {app_name}", default_return=None)
    def get_backup():
        return web_client.web_apps.get_backup_configuration(
            resource_group_name=app_dict['resource_group_name'],
            name=app_name
        )
    
    return get_backup()


def _get_deployment_slots(
    web_client: Any,
    app_dict: Dict[str, Any],
    app_name: str
) -> List[Dict[str, Any]]:
    """Get deployment slots with error handling."""
    @safe_azure_operation(f"list deployment slots for {app_name}", default_return=[])
    def list_slots():
        slots = list(web_client.web_apps.list_slots(
            resource_group_name=app_dict['resource_group_name'],
            name=app_name
        ))
        return [format_resource_dict(slot, 'deployment_slot') for slot in slots]
    
    return list_slots()


# CLI Commands
@app.command("scan-plans")
def scan_app_service_plans_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure App Service Plans and generates Terraform code."""
    typer.echo(f"Scanning for Azure App Service Plans in subscription '{subscription_id}'...")
    
    try:
        scan_app_service_plans(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning App Service Plans: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("scan-apps")
def scan_web_apps_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure Web Apps and generates Terraform code."""
    typer.echo(f"Scanning for Azure Web Apps in subscription '{subscription_id}'...")
    
    try:
        scan_web_apps(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning Web Apps: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list-plans")
def list_app_service_plans(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all App Service Plan resources previously generated."""
    ImportManager(output_dir, "azure_app_service_plan").list_all()


@app.command("import-plan")
def import_app_service_plan(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the App Service Plan to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific App Service Plan."""
    ImportManager(output_dir, "azure_app_service_plan").find_and_import(resource_id)


@app.command("list-apps")
def list_web_apps(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all Web App resources previously generated."""
    ImportManager(output_dir, "azure_web_app").list_all()


@app.command("import-app")
def import_web_app(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Web App to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific Web App."""
    ImportManager(output_dir, "azure_web_app").find_and_import(resource_id)
