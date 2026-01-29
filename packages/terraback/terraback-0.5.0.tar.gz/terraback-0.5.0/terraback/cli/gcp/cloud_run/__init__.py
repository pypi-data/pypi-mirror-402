import typer
from pathlib import Path
from typing import Optional
from terraback.core.license import require_professional

from . import services

app = typer.Typer(
    name="cloud-run",
    help="Work with GCP Cloud Run resources.",
    no_args_is_help=True,
)

def register():
    """Register Cloud Run scan functions with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    from .services import scan_cloud_run_services
    
    register_scan_function("gcp_cloud_run_service", scan_cloud_run_services)

# Add sub-commands
app.add_typer(services.app, name="service")

@app.command("scan-all")
@require_professional
def scan_all_services(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", envvar="GOOGLE_CLOUD_PROJECT"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan all GCP Cloud Run resources."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GOOGLE_CLOUD_PROJECT", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan("gcp_cloud_run_service", output_dir=output_dir, project_id=project_id)
    else:
        from .services import scan_cloud_run_services_command
        
        # Call the command function with the proper parameters
        if not project_id:
            project_id = get_default_project_id()
        
        services_data = services.get_cloud_run_services_data(project_id)
        if services_data:
            from terraback.terraform_generator.writer import generate_tf
            from terraback.terraform_generator.imports import generate_imports_file
            
            output_file = output_dir / "gcp_cloud_run_service.tf"
            generate_tf(services_data, "gcp_cloud_run_service", output_file, provider="gcp", project_id=project_id)
            generate_imports_file("gcp_cloud_run_service", services_data, remote_resource_id_key="name", output_dir=output_dir, provider="gcp")
            typer.echo(f"Generated Terraform for {len(services_data)} Cloud Run services -> {output_file}")