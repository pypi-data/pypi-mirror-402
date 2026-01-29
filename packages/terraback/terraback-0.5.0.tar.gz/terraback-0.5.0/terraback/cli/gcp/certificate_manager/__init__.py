import typer
from pathlib import Path
from typing import Optional
from terraback.core.license import require_professional

from . import certificates, certificate_maps

app = typer.Typer(
    name="certificate-manager",
    help="Work with GCP Certificate Manager resources.",
    no_args_is_help=True,
)

def register():
    """Register Certificate Manager scan functions with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    from .certificates import scan_certificates
    from .certificate_maps import scan_certificate_maps
    
    register_scan_function("gcp_certificate", scan_certificates)
    register_scan_function("gcp_certificate_map", scan_certificate_maps)

# Add sub-commands
app.add_typer(certificates.app, name="certificate")
app.add_typer(certificate_maps.app, name="certificate-map")

@app.command("scan-all")
@require_professional
def scan_all_certificates(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", envvar="GOOGLE_CLOUD_PROJECT"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan all GCP Certificate Manager resources."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GOOGLE_CLOUD_PROJECT", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan("gcp_certificate", output_dir=output_dir, project_id=project_id)
    else:
        from .certificates import scan_certificates
        from .certificate_maps import scan_certificate_maps
        
        scan_certificates(output_dir=output_dir, project_id=project_id, with_deps=False)
        scan_certificate_maps(output_dir=output_dir, project_id=project_id, with_deps=False)