from terraback.core.license import require_professional
import typer
from pathlib import Path

from .memorystore_redis import scan_memorystore_redis, list_memorystore_redis, import_memorystore_redis
from .memorystore_memcached import scan_memorystore_memcached, list_memorystore_memcached, import_memorystore_memcached

from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

app = typer.Typer(
    name="caching",
    help="Manage GCP caching resources like Memorystore for Redis and Memcached.",
    no_args_is_help=True
)

# --- Memorystore Redis Commands ---
@app.command(name="scan-redis", help="Scan Memorystore Redis instances.")
@require_professional
def scan_redis_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    region: str = typer.Option(None, help="GCP region")
):
    scan_memorystore_redis(output_dir, project_id, region)

@app.command(name="list-redis", help="List scanned Memorystore Redis instances.")
@require_professional
def list_redis_command(output_dir: Path = typer.Option("generated")):
    list_memorystore_redis(output_dir)

@app.command(name="import-redis", help="Import a Memorystore Redis instance by ID.")
@require_professional
def import_redis_command(
    instance_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_memorystore_redis(instance_id, output_dir)

# --- Memorystore Memcached Commands ---
@app.command(name="scan-memcached", help="Scan Memorystore Memcached instances.")
@require_professional
def scan_memcached_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    region: str = typer.Option(None, help="GCP region")
):
    scan_memorystore_memcached(output_dir, project_id, region)

@app.command(name="list-memcached", help="List scanned Memorystore Memcached instances.")
@require_professional
def list_memcached_command(output_dir: Path = typer.Option("generated")):
    list_memorystore_memcached(output_dir)

@app.command(name="import-memcached", help="Import a Memorystore Memcached instance by ID.")
@require_professional
def import_memcached_command(
    instance_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_memorystore_memcached(instance_id, output_dir)

# --- Combined Commands ---
@app.command(name="scan-all", help="Scan all Memorystore resources.")
@require_professional
def scan_all_memorystore_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    project_id: str = typer.Option(None, help="GCP Project ID"),
    region: str = typer.Option(None, help="GCP region")
):
    scan_memorystore_redis(output_dir, project_id, region)
    scan_memorystore_memcached(output_dir, project_id, region)

# --- Registration ---
def register():
    """Registers scan functions and dependencies for the Memorystore module."""
    register_scan_function("gcp_memorystore_redis", scan_memorystore_redis)
    register_scan_function("gcp_memorystore_memcached", scan_memorystore_memcached)

    # Define Memorystore dependencies
    # Instances depend on VPC networking
    cross_scan_registry.register_dependency("gcp_memorystore_redis", "gcp_network")
    cross_scan_registry.register_dependency("gcp_memorystore_redis", "gcp_subnet")
    cross_scan_registry.register_dependency("gcp_memorystore_memcached", "gcp_network")
    cross_scan_registry.register_dependency("gcp_memorystore_memcached", "gcp_subnet")
    
    # Instances may depend on service accounts for auth
    cross_scan_registry.register_dependency("gcp_memorystore_redis", "gcp_service_account")
    cross_scan_registry.register_dependency("gcp_memorystore_memcached", "gcp_service_account")