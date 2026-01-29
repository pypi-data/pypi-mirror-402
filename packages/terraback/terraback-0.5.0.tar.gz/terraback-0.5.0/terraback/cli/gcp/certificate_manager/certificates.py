# terraback/cli/gcp/certificate_manager/certificates.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any

from terraback.cli.gcp.session import get_gcp_client, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="certificate", help="Scan and import GCP Certificate Manager certificates.")

def get_certificate_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch Certificate Manager certificate data from GCP."""
    # Temporary placeholder - Certificate Manager API requires additional setup
    typer.echo("Certificate Manager scanning is temporarily unavailable. Please check back later.")
    return []

@app.command("scan")
def scan_certificates(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
):
    """Scans GCP Certificate Manager certificates and generates Terraform code."""
    # Get default project if not provided
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please set GCP_PROJECT_ID or use --project-id", err=True)
            raise typer.Exit(code=1)
    
    typer.echo(f"Scanning for Certificate Manager certificates in project '{project_id}'...")
    
    certificates = get_certificate_data(project_id)
    
    if not certificates:
        typer.echo("No certificates found or feature temporarily unavailable.")
        return
    
    # Generate Terraform files
    output_file = output_dir / "gcp_certificate_manager_certificate.tf"
    generate_tf(certificates, "gcp_certificate_manager_certificate", output_file, provider="gcp")
    typer.echo(f"Generated Terraform for {len(certificates)} certificates -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_certificate_manager_certificate",
        certificates,
        remote_resource_id_key="name",
        output_dir=output_dir,
        provider="gcp"
    )

@app.command("list")
def list_certificates(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Lists all certificate resources previously generated."""
    ImportManager(output_dir, "gcp_certificate_manager_certificate").list_all()

@app.command("import")
def import_certificate(
    certificate_name: str = typer.Argument(..., help="Certificate name to import."),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing generated files.")
):
    """Runs terraform import for a specific certificate by its name."""
    ImportManager(output_dir, "gcp_certificate_manager_certificate").find_and_import(certificate_name)

# Scan function for cross-scan registry
def scan_certificates(
    output_dir: Path,
    project_id: str = None,
    region: str = None,
    zone: str = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning Certificate Manager certificates in project {project_id}")
    
    certificates = get_certificate_data(project_id)
    
    if certificates:
        output_file = output_dir / "gcp_certificate_manager_certificate.tf"
        generate_tf(certificates, "gcp_certificate_manager_certificate", output_file, provider="gcp")
        generate_imports_file(
            "gcp_certificate_manager_certificate",
            certificates,
            remote_resource_id_key="name",
            output_dir=output_dir,
            provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(certificates)} Certificate Manager certificates")