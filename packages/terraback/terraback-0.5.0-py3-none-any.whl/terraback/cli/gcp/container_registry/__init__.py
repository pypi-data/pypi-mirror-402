import typer
from pathlib import Path
from typing import Optional
from terraback.core.license import require_professional

from . import registries

app = typer.Typer(
    name="container-registry",
    help="Work with GCP Container Registry resources.",
    no_args_is_help=True,
)

def register():
    """Register Container Registry scan functions with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    from .registries import scan_container_registries
    
    register_scan_function("gcp_container_registry", scan_container_registries)

# Add sub-commands
app.add_typer(registries.app, name="registry")

@app.command("scan-all")
@require_professional
def scan_all_registries(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", envvar="GOOGLE_CLOUD_PROJECT"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan all GCP Container Registry resources."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GOOGLE_CLOUD_PROJECT", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan("gcp_container_registry", output_dir=output_dir, project_id=project_id)
    else:
        from .registries import scan_container_registries_legacy
        
        scan_container_registries_legacy(output_dir=output_dir, project_id=project_id, with_deps=False)