import typer
from pathlib import Path
from typing import Optional
from terraback.core.license import require_professional

from . import cloud_functions

app = typer.Typer(
    name="functions",
    help="Work with GCP Cloud Functions resources.",
    no_args_is_help=True,
)

def register():
    """Register Cloud Functions scan functions with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function
    
    from .cloud_functions import scan_cloud_functions
    
    register_scan_function("gcp_cloud_function", scan_cloud_functions)

# Add sub-commands
app.add_typer(cloud_functions.app, name="function")

@app.command("scan-all")
@require_professional
def scan_all_functions(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", envvar="GOOGLE_CLOUD_PROJECT"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan all GCP Cloud Functions resources."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GOOGLE_CLOUD_PROJECT", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan("gcp_cloud_function", output_dir=output_dir, project_id=project_id)
    else:
        from .cloud_functions import scan_cloud_functions
        
        scan_cloud_functions(output_dir=output_dir, project_id=project_id, with_deps=False)