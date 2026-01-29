# terraback/cli/gcp/sql/instances.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="instance", help="Scan and import GCP Cloud SQL instances.")

def get_sql_instance_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch Cloud SQL instance data from GCP."""
    credentials = get_gcp_credentials()
    service = discovery.build('sqladmin', 'v1', credentials=credentials)
    
    sql_instances = []
    
    try:
        # List all SQL instances in the project
        request = service.instances().list(project=project_id)
        response = request.execute()
        
        for instance in response.get('items', []):
            # Get instance details
            instance_data = {
                "name": instance.get('name'),
                "project": project_id,
                "region": instance.get('region'),
                "database_version": instance.get('databaseVersion'),
                "name_sanitized": instance.get('name', '').replace('-', '_').lower(),
            }
            
            # Get settings
            if instance.get('settings'):
                settings = instance['settings']
                instance_data["settings"] = {
                    "tier": settings.get('tier'),
                    # Read actual values instead of hardcoded defaults
                    "activation_policy": settings.get('activationPolicy'),
                    "availability_type": settings.get('availabilityType'),  
                    "pricing_plan": settings.get('pricingPlan'),
                }
                
                # Disk configuration - read actual values
                if 'dataDiskType' in settings:
                    instance_data["settings"]["disk_type"] = settings['dataDiskType']
                if 'dataDiskSizeGb' in settings:
                    instance_data["settings"]["disk_size"] = settings['dataDiskSizeGb']
                if 'storageAutoResize' in settings:
                    instance_data["settings"]["disk_autoresize"] = settings['storageAutoResize']
                if settings.get('storageAutoResizeLimit'):
                    instance_data["settings"]["disk_autoresize_limit"] = settings['storageAutoResizeLimit']
                
                # Backup configuration
                if settings.get('backupConfiguration'):
                    backup = settings['backupConfiguration']
                    backup_config = {
                        "enabled": backup.get('enabled', False),
                        "start_time": backup.get('startTime', '23:00'),
                    }
                    if backup.get('pointInTimeRecoveryEnabled') is not None:
                        backup_config["point_in_time_recovery_enabled"] = backup['pointInTimeRecoveryEnabled']
                    if backup.get('transactionLogRetentionDays'):
                        backup_config["transaction_log_retention_days"] = backup['transactionLogRetentionDays']
                    if backup.get('location'):
                        backup_config["location"] = backup['location']
                    instance_data["settings"]["backup_configuration"] = backup_config
                
                # IP configuration
                if settings.get('ipConfiguration'):
                    ip_config = settings['ipConfiguration']
                    ip_data = {
                        "ipv4_enabled": ip_config.get('ipv4Enabled', True),
                        "private_network": ip_config.get('privateNetwork'),
                        "require_ssl": ip_config.get('requireSsl', False),
                    }
                    
                    # Authorized networks
                    if ip_config.get('authorizedNetworks'):
                        ip_data["authorized_networks"] = []
                        for network in ip_config['authorizedNetworks']:
                            ip_data["authorized_networks"].append({
                                "name": network.get('name', ''),
                                "value": network.get('value', ''),
                                "expiration_time": network.get('expirationTime'),
                            })
                    
                    instance_data["settings"]["ip_configuration"] = ip_data
                
                # Database flags
                if settings.get('databaseFlags'):
                    instance_data["settings"]["database_flags"] = []
                    for flag in settings['databaseFlags']:
                        instance_data["settings"]["database_flags"].append({
                            "name": flag.get('name'),
                            "value": flag.get('value'),
                        })
                
                # User labels
                if settings.get('userLabels'):
                    instance_data["settings"]["user_labels"] = settings['userLabels']
                
                # Maintenance window
                if settings.get('maintenanceWindow'):
                    maint = settings['maintenanceWindow']
                    instance_data["settings"]["maintenance_window"] = {
                        "day": maint.get('day'),
                        "hour": maint.get('hour'),
                        "update_track": maint.get('updateTrack', 'stable'),
                    }
                
                # Insights config
                if settings.get('insightsConfig'):
                    insights = settings['insightsConfig']
                    instance_data["settings"]["insights_config"] = {
                        "query_insights_enabled": insights.get('queryInsightsEnabled', False),
                        "record_application_tags": insights.get('recordApplicationTags', False),
                        "record_client_address": insights.get('recordClientAddress', False),
                        "query_string_length": insights.get('queryStringLength', 1024),
                    }
            
            # Connection information
            instance_data["connection_name"] = instance.get('connectionName')
            instance_data["ip_addresses"] = []
            if instance.get('ipAddresses'):
                for ip in instance['ipAddresses']:
                    instance_data["ip_addresses"].append({
                        "type": ip.get('type'),
                        "ip_address": ip.get('ipAddress'),
                    })
            
            # State information
            instance_data["state"] = instance.get('state')
            instance_data["backend_type"] = instance.get('backendType', 'SECOND_GEN')
            
            # Root password (if set)
            if instance.get('rootPassword'):
                instance_data["root_password"] = instance['rootPassword']
            
            # Replica configuration
            if instance.get('replicaConfiguration'):
                instance_data["replica_configuration"] = instance['replicaConfiguration']
            
            # Master instance name (for replicas)
            if instance.get('masterInstanceName'):
                instance_data["master_instance_name"] = instance['masterInstanceName']
            
            sql_instances.append(instance_data)
    
    except HttpError as e:
        if e.resp.status == 403:
            typer.echo(f"Permission denied. Make sure the Cloud SQL Admin API is enabled and you have the necessary permissions.")
        else:
            typer.echo(f"Error fetching SQL instances: {e}")
    except Exception as e:
        typer.echo(f"Unexpected error: {e}")
    
    return sql_instances

@app.command("scan")
def scan_sql_instances(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
):
    """Scans GCP Cloud SQL instances and generates Terraform code."""
    # Get default project if not provided
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please set GCP_PROJECT_ID or use --project-id", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning for Cloud SQL instances in project '{project_id}'...")
    
    sql_instances = get_sql_instance_data(project_id)
    
    if not sql_instances:
        typer.echo("No Cloud SQL instances found.")
        return
    
    # Generate Terraform files
    output_file = output_dir / "gcp_sql_instance.tf"
    generate_tf(sql_instances, "gcp_sql_instance", output_file, provider="gcp")
    typer.echo(f"Generated Terraform for {len(sql_instances)} Cloud SQL instances -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_sql_instance",
        sql_instances,
        remote_resource_id_key="name",
        output_dir=output_dir,
        provider="gcp"
    )

@app.command("list")
def list_sql_instances(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Lists all Cloud SQL instance resources previously generated."""
    ImportManager(output_dir, "gcp_sql_instance").list_all()

@app.command("import")
def import_sql_instance(
    instance_name: str = typer.Argument(..., help="Cloud SQL instance name to import."),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Runs terraform import for a specific Cloud SQL instance by its name."""
    ImportManager(output_dir, "gcp_sql_instance").find_and_import(instance_name)

# Register with cross-scan if needed
def register():
    """Register Cloud SQL instances with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    # Create a partial function that matches the expected signature
    from functools import partial
    scan_func = partial(
        scan_sql_instances_for_registry,
        output_dir=Path("generated")
    )
    register_scan_function("gcp_sql_instance", scan_func)

def scan_sql_instances_for_registry(
    output_dir: Path,
    project_id: str = None,
    **kwargs
):
    """Scan function for cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    sql_instances = get_sql_instance_data(project_id)
    
    if sql_instances:
        output_file = output_dir / "gcp_sql_instance.tf"
        generate_tf(sql_instances, "gcp_sql_instance", output_file, provider="gcp")
        
        generate_imports_file(
            "gcp_sql_instance",
            sql_instances,
            remote_resource_id_key="name",
            output_dir=output_dir,
            provider="gcp"
        )