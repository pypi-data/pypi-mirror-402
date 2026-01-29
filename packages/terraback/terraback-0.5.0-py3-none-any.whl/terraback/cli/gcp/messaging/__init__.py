from terraback.core.license import require_professional
import typer
from pathlib import Path

from .cloud_tasks import scan_cloud_tasks_queues, list_cloud_tasks_queues, import_cloud_tasks_queue

from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

app = typer.Typer(
    name="messaging",
    help="Manage GCP messaging resources like Cloud Tasks queues.",
    no_args_is_help=True
)

# --- Cloud Tasks Queue Commands ---
@app.command(name="scan-queues", help="Scan Cloud Tasks queues.")
@require_professional
def scan_queues_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_cloud_tasks_queues(output_dir, project_id, location)

@app.command(name="list-queues", help="List scanned Cloud Tasks queues.")
@require_professional
def list_queues_command(output_dir: Path = typer.Option("generated")):
    list_cloud_tasks_queues(output_dir)

@app.command(name="import-queue", help="Import a Cloud Tasks queue by ID.")
@require_professional
def import_queue_command(
    queue_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_cloud_tasks_queue(queue_id, output_dir)

# --- Combined Commands ---
@app.command(name="scan-all", help="Scan all Cloud Tasks resources.")
@require_professional
def scan_all_cloud_tasks_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_cloud_tasks_queues(output_dir, project_id, location)

# --- Registration ---
def register():
    """Registers scan functions and dependencies for the Cloud Tasks module."""
    register_scan_function("gcp_cloud_tasks_queue", scan_cloud_tasks_queues)

    # Define Cloud Tasks dependencies
    # Queues may depend on service accounts for task execution
    cross_scan_registry.register_dependency("gcp_cloud_tasks_queue", "gcp_service_account")
    
    # Queues may use VPC for private endpoints
    cross_scan_registry.register_dependency("gcp_cloud_tasks_queue", "gcp_network")