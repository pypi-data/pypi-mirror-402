from terraback.core.license import require_professional
import typer
from pathlib import Path

from .api_gateway import scan_api_gateways, list_api_gateways, import_api_gateway
from .workflows import scan_workflows, list_workflows, import_workflow
from .eventarc import scan_eventarc_triggers, list_eventarc_triggers, import_eventarc_trigger

from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

app = typer.Typer(
    name="integration",
    help="Manage GCP integration resources like API Gateway, Workflows, and Eventarc.",
    no_args_is_help=True
)

# --- API Gateway Commands ---
@app.command(name="scan-api-gateway", help="Scan API Gateway resources.")
@require_professional
def scan_api_gateway_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_api_gateways(output_dir, project_id, location)

@app.command(name="list-api-gateway", help="List scanned API Gateway resources.")
@require_professional
def list_api_gateway_command(output_dir: Path = typer.Option("generated")):
    list_api_gateways(output_dir)

@app.command(name="import-api-gateway", help="Import an API Gateway resource by ID.")
@require_professional
def import_api_gateway_command(
    resource_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_api_gateway(resource_id, output_dir)

# --- Workflows Commands ---
@app.command(name="scan-workflows", help="Scan Workflows.")
@require_professional
def scan_workflows_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_workflows(output_dir, project_id, location)

@app.command(name="list-workflows", help="List scanned Workflows.")
@require_professional
def list_workflows_command(output_dir: Path = typer.Option("generated")):
    list_workflows(output_dir)

@app.command(name="import-workflow", help="Import a Workflow by ID.")
@require_professional
def import_workflow_command(
    workflow_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_workflow(workflow_id, output_dir)

# --- Eventarc Commands ---
@app.command(name="scan-eventarc", help="Scan Eventarc triggers.")
@require_professional
def scan_eventarc_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_eventarc_triggers(output_dir, project_id, location)

@app.command(name="list-eventarc", help="List scanned Eventarc triggers.")
@require_professional
def list_eventarc_command(output_dir: Path = typer.Option("generated")):
    list_eventarc_triggers(output_dir)

@app.command(name="import-eventarc", help="Import an Eventarc trigger by ID.")
@require_professional
def import_eventarc_command(
    trigger_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_eventarc_trigger(trigger_id, output_dir)

# --- Combined Commands ---
@app.command(name="scan-all", help="Scan all integration resources.")
@require_professional
def scan_all_integration_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    location: str = typer.Option(None, help="GCP location/region")
):
    scan_api_gateways(output_dir, project_id, location)
    scan_workflows(output_dir, project_id, location)
    scan_eventarc_triggers(output_dir, project_id, location)

# --- Registration ---
def register():
    """Registers scan functions and dependencies for the integration module."""
    register_scan_function("gcp_api_gateway", scan_api_gateways)
    register_scan_function("gcp_workflows", scan_workflows)
    register_scan_function("gcp_eventarc_trigger", scan_eventarc_triggers)

    # Define integration dependencies
    # API Gateway may use service accounts
    cross_scan_registry.register_dependency("gcp_api_gateway", "gcp_service_account")
    
    # Workflows need service accounts for execution
    cross_scan_registry.register_dependency("gcp_workflows", "gcp_service_account")
    
    # Eventarc triggers may depend on Pub/Sub topics
    cross_scan_registry.register_dependency("gcp_eventarc_trigger", "gcp_pubsub_topic")
    cross_scan_registry.register_dependency("gcp_eventarc_trigger", "gcp_service_account")
    
    # Eventarc may trigger Cloud Run services or Cloud Functions
    cross_scan_registry.register_dependency("gcp_eventarc_trigger", "gcp_cloud_run_service")
    cross_scan_registry.register_dependency("gcp_eventarc_trigger", "gcp_cloud_function")