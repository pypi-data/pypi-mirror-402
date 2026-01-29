# terraback/cli/gcp/functions/cloud_functions.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any

from terraback.cli.gcp.session import get_gcp_client, get_default_project_id, get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="function", help="Scan and import GCP Cloud Functions.")

def get_cloud_function_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch Cloud Function data from GCP."""
    # Temporary placeholder - Cloud Functions API requires additional setup
    typer.echo("Cloud Functions scanning is temporarily unavailable. Please check back later.")
    return []

@app.command("scan")
def scan_cloud_functions(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="GCP region to scan."),
):
    """Scans GCP Cloud Functions and generates Terraform code."""
    # Get default project if not provided
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please set GCP_PROJECT_ID or use --project-id", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning for Cloud Functions in project '{project_id}'...")
    if region:
        typer.echo(f"Filtering by region: {region}")
    
    functions = get_cloud_function_data(project_id, region)
    
    if not functions:
        typer.echo("No Cloud Functions found or feature temporarily unavailable.")
        return
    
    # Generate Terraform files
    output_file = output_dir / "gcp_cloudfunctions_function.tf"
    generate_tf(functions, "gcp_cloudfunctions_function", output_file, provider="gcp")
    typer.echo(f"Generated Terraform for {len(functions)} Cloud Functions -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_cloudfunctions_function",
        functions,
        remote_resource_id_key="name",
        output_dir=output_dir,
        provider="gcp"
    )

@app.command("list")
def list_cloud_functions(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Lists all Cloud Function resources previously generated."""
    ImportManager(output_dir, "gcp_cloudfunctions_function").list_all()

@app.command("import")
def import_cloud_function(
    function_name: str = typer.Argument(..., help="Cloud Function name to import."),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Runs terraform import for a specific Cloud Function by its name."""
    ImportManager(output_dir, "gcp_cloudfunctions_function").find_and_import(function_name)

# Scan function for cross-scan registry
def scan_cloud_functions(
    output_dir: Path,
    project_id: str = None,
    region: str = None,
    zone: str = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning Cloud Functions in project {project_id}")
    if region:
        typer.echo(f"[Cross-scan] Filtering by region: {region}")
    
    functions = get_cloud_function_data(project_id, region)
    
    if functions:
        output_file = output_dir / "gcp_cloudfunctions_function.tf"
        generate_tf(functions, "gcp_cloudfunctions_function", output_file, provider="gcp")
        generate_imports_file(
            "gcp_cloudfunctions_function",
            functions,
            remote_resource_id_key="name",
            output_dir=output_dir,
            provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(functions)} Cloud Functions")