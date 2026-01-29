# terraback/cli/gcp/sql/databases.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from .instances import get_sql_instance_data

app = typer.Typer(name="database", help="Scan and import GCP Cloud SQL databases.")

def get_sql_database_data(project_id: str, instance_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch Cloud SQL database data from GCP."""
    credentials = get_gcp_credentials()
    service = discovery.build('sqladmin', 'v1', credentials=credentials)
    
    sql_databases = []
    
    try:
        # First get all instances (or filter by instance name)
        instances = []
        if instance_name:
            # Get specific instance
            try:
                instance = service.instances().get(project=project_id, instance=instance_name).execute()
                instances = [instance]
            except HttpError as e:
                if e.resp.status == 404:
                    typer.echo(f"Instance '{instance_name}' not found in project '{project_id}'")
                else:
                    typer.echo(f"Error fetching instance '{instance_name}': {e}")
                return []
        else:
            # Get all instances
            response = service.instances().list(project=project_id).execute()
            instances = response.get('items', [])
        
        # For each instance, get its databases
        for instance in instances:
            inst_name = instance.get('name')
            
            try:
                # List databases for this instance
                db_response = service.databases().list(project=project_id, instance=inst_name).execute()
                
                for database in db_response.get('items', []):
                    # Skip system databases
                    db_name = database.get('name')
                    if db_name in ['mysql', 'information_schema', 'performance_schema', 'sys', 'postgres', 'template0', 'template1']:
                        continue
                    
                    database_data = {
                        "name": db_name,
                        "instance": inst_name,
                        "project": project_id,
                        "charset": database.get('charset', 'utf8'),
                        "collation": database.get('collation'),
                        "name_sanitized": f"{inst_name}_{db_name}".replace('-', '_').replace('.', '_').lower(),
                        # For import, we need the composite ID
                        "import_id": f"{inst_name}:{db_name}",
                    }
                    
                    # Add instance region for context
                    database_data["instance_region"] = instance.get('region')
                    
                    # Database version from instance
                    database_data["database_version"] = instance.get('databaseVersion')
                    
                    sql_databases.append(database_data)
            
            except HttpError as e:
                typer.echo(f"Error fetching databases for instance '{inst_name}': {e}")
                continue
    
    except HttpError as e:
        if e.resp.status == 403:
            typer.echo(f"Permission denied. Make sure the Cloud SQL Admin API is enabled and you have the necessary permissions.")
        else:
            typer.echo(f"Error fetching SQL instances: {e}")
    except Exception as e:
        typer.echo(f"Unexpected error: {e}")
    
    return sql_databases

@app.command("scan")
def scan_sql_databases(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    instance_name: Optional[str] = typer.Option(None, "--instance", "-i", help="Filter by specific SQL instance name."),
):
    """Scans GCP Cloud SQL databases and generates Terraform code."""
    # Get default project if not provided
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please set GCP_PROJECT_ID or use --project-id", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning for Cloud SQL databases in project '{project_id}'...")
    if instance_name:
        typer.echo(f"Filtering by instance: {instance_name}")
    
    sql_databases = get_sql_database_data(project_id, instance_name)
    
    if not sql_databases:
        typer.echo("No Cloud SQL databases found.")
        return
    
    # Generate Terraform files
    output_file = output_dir / "gcp_sql_database.tf"
    generate_tf(sql_databases, "gcp_sql_database", output_file, provider="gcp")
    typer.echo(f"Generated Terraform for {len(sql_databases)} Cloud SQL databases -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_sql_database",
        sql_databases,
        remote_resource_id_key="import_id",
        output_dir=output_dir,
        provider="gcp"
    )

@app.command("list")
def list_sql_databases(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Lists all Cloud SQL database resources previously generated."""
    ImportManager(output_dir, "gcp_sql_database").list_all()

@app.command("import")
def import_sql_database(
    database_id: str = typer.Argument(..., help="Cloud SQL database ID to import (format: instance_name:database_name)."),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Runs terraform import for a specific Cloud SQL database by its ID."""
    ImportManager(output_dir, "gcp_sql_database").find_and_import(database_id)

# Register with cross-scan if needed
def register():
    """Register Cloud SQL databases with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    # Create a partial function that matches the expected signature
    from functools import partial
    scan_func = partial(
        scan_sql_databases_for_registry,
        output_dir=Path("generated")
    )
    register_scan_function("gcp_sql_database", scan_func)

def scan_sql_databases_for_registry(
    output_dir: Path,
    project_id: str = None,
    instance_name: str = None,
    **kwargs
):
    """Scan function for cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    sql_databases = get_sql_database_data(project_id, instance_name)
    
    if sql_databases:
        output_file = output_dir / "gcp_sql_database.tf"
        generate_tf(sql_databases, "gcp_sql_database", output_file, provider="gcp")
        
        generate_imports_file(
            "gcp_sql_database",
            sql_databases,
            remote_resource_id_key="import_id",
            output_dir=output_dir,
            provider="gcp"
        )

# Alias for backward compatibility with cross-scan registry
scan_gcp_sql_databases = scan_sql_databases_for_registry