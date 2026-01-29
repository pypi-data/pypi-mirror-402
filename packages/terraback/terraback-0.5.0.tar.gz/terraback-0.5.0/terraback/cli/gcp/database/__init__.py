from terraback.core.license import require_professional
import typer
from pathlib import Path

from .firestore import scan_firestore_databases, list_firestore_databases, import_firestore_database
from .bigtable import scan_bigtable_instances, list_bigtable_instances, import_bigtable_instance
from .spanner import scan_spanner_instances, list_spanner_instances, import_spanner_instance

from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

app = typer.Typer(
    name="database",
    help="Manage GCP database resources like Firestore, Bigtable, and Spanner.",
    no_args_is_help=True
)

# --- Firestore Commands ---
@app.command(name="scan-firestore", help="Scan Firestore databases.")
@require_professional
def scan_firestore_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID")
):
    scan_firestore_databases(output_dir, project_id)

@app.command(name="list-firestore", help="List scanned Firestore databases.")
@require_professional
def list_firestore_command(output_dir: Path = typer.Option("generated")):
    list_firestore_databases(output_dir)

@app.command(name="import-firestore", help="Import a Firestore database by ID.")
@require_professional
def import_firestore_command(
    database_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_firestore_database(database_id, output_dir)

# --- Bigtable Commands ---
@app.command(name="scan-bigtable", help="Scan Bigtable instances.")
@require_professional
def scan_bigtable_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID")
):
    scan_bigtable_instances(output_dir, project_id)

@app.command(name="list-bigtable", help="List scanned Bigtable instances.")
@require_professional
def list_bigtable_command(output_dir: Path = typer.Option("generated")):
    list_bigtable_instances(output_dir)

@app.command(name="import-bigtable", help="Import a Bigtable instance by ID.")
@require_professional
def import_bigtable_command(
    instance_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_bigtable_instance(instance_id, output_dir)

# --- Spanner Commands ---
@app.command(name="scan-spanner", help="Scan Spanner instances.")
@require_professional
def scan_spanner_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID")
):
    scan_spanner_instances(output_dir, project_id)

@app.command(name="list-spanner", help="List scanned Spanner instances.")
@require_professional
def list_spanner_command(output_dir: Path = typer.Option("generated")):
    list_spanner_instances(output_dir)

@app.command(name="import-spanner", help="Import a Spanner instance by ID.")
@require_professional
def import_spanner_command(
    instance_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_spanner_instance(instance_id, output_dir)

# --- Combined Commands ---
@app.command(name="scan-all", help="Scan all NoSQL and NewSQL database resources.")
@require_professional
def scan_all_databases_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID")
):
    scan_firestore_databases(output_dir, project_id)
    scan_bigtable_instances(output_dir, project_id)
    scan_spanner_instances(output_dir, project_id)

# --- Registration ---
def register():
    """Registers scan functions and dependencies for the database module."""
    register_scan_function("gcp_firestore_database", scan_firestore_databases)
    register_scan_function("gcp_bigtable_instance", scan_bigtable_instances)
    register_scan_function("gcp_spanner_instance", scan_spanner_instances)

    # Define database dependencies
    # Bigtable instances may use KMS for encryption
    cross_scan_registry.register_dependency("gcp_bigtable_instance", "gcp_kms_crypto_key")
    
    # Spanner instances may use KMS for encryption
    cross_scan_registry.register_dependency("gcp_spanner_instance", "gcp_kms_crypto_key")
    
    # Databases may need IAM service accounts
    cross_scan_registry.register_dependency("gcp_firestore_database", "gcp_service_account")
    cross_scan_registry.register_dependency("gcp_bigtable_instance", "gcp_service_account")
    cross_scan_registry.register_dependency("gcp_spanner_instance", "gcp_service_account")