# terraback/cli/gcp/cloud_run/services.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import run_v2
from google.api_core import exceptions

from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

app = typer.Typer(name="cloud-run", help="Scan and import GCP Cloud Run services.")

def get_cloud_run_services_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Cloud Run services data from GCP.
    
    Args:
        project_id: GCP project ID
        region: Optional region filter
    
    Returns:
        List of Cloud Run service data dictionaries
    """
    def _scan_cloud_run():
        session = get_gcp_credentials()
        client = run_v2.ServicesClient(credentials=session)
        
        services = []
        seen_services = set()  # Track service names to avoid duplicates
        regions_to_scan = []
        debug_regions = []  # Track which regions we find services in
        
        if region:
            regions_to_scan = [region]
        else:
            # Common Cloud Run regions
            regions_to_scan = [
                "us-central1", "us-west1", "us-west2", "us-west3", "us-west4",
                "us-east1", "us-east4", "us-east5", "us-south1",
                "europe-west1", "europe-west2", "europe-west3", "europe-west4", 
                "europe-west6", "europe-west8", "europe-west9", "europe-west12",
                "europe-central2", "europe-north1", "europe-southwest1",
                "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2", 
                "asia-northeast3", "asia-south1", "asia-south2", "asia-southeast1", 
                "asia-southeast2", "australia-southeast1", "australia-southeast2",
                "northamerica-northeast1", "northamerica-northeast2",
                "southamerica-east1", "southamerica-west1",
                "me-central1", "me-west1"
            ]
        
        for scan_region in regions_to_scan:
            try:
                parent = f"projects/{project_id}/locations/{scan_region}"
                request = run_v2.ListServicesRequest(parent=parent)
                
                for service in client.list_services(request=request):
                    # Extract service data
                    service_name = service.name.split('/')[-1]
                    full_service_path = service.name  # Full path like: projects/PROJECT/locations/REGION/services/NAME
                    
                    # Track regions where we find services for debugging
                    debug_regions.append(f"{scan_region}:{service_name}")
                    
                    # AGGRESSIVE deduplication - Skip if we've seen this service name (not just path)
                    if service_name in seen_services:
                        print(f"SKIPPING duplicate service: {service_name} in {scan_region}")
                        continue
                    seen_services.add(service_name)
                    print(f"ADDING service: {service_name} in {scan_region}")
                    
                    # For Cloud Run v2, the import format is: locations/<location>/namespaces/<project>/services/<name>
                    import_id = f"locations/{scan_region}/namespaces/{project_id}/services/{service_name}"
                    
                    service_data = {
                        "name": service_name,
                        "full_name": service.name,  # Store full resource path for API calls
                        "import_id": import_id,     # Store correct import ID format
                        "location": scan_region,
                        "project": project_id,
                        "name_sanitized": service_name.replace('-', '_').lower(),
                    }
                    
                    # Extract container configuration
                    if service.template and service.template.containers:
                        container = service.template.containers[0]  # Usually only one container
                        service_data["container_image"] = container.image
                        
                        # Container ports
                        if container.ports:
                            service_data["container_ports"] = []
                            for port in container.ports:
                                port_data = {"container_port": port.container_port}
                                if hasattr(port, 'name') and port.name:
                                    port_data["name"] = port.name
                                service_data["container_ports"].append(port_data)
                        
                        # Environment variables
                        if container.env:
                            service_data["container_env_vars"] = []
                            for env in container.env:
                                if hasattr(env, 'value') and env.value:
                                    service_data["container_env_vars"].append({
                                        "name": env.name,
                                        "value": env.value
                                    })
                        
                        # Resources
                        if container.resources:
                            resources = {}
                            if container.resources.limits:
                                resources["limits"] = dict(container.resources.limits)
                            if hasattr(container.resources, 'requests') and container.resources.requests:
                                resources["requests"] = dict(container.resources.requests)
                            if resources:
                                service_data["container_resources"] = resources
                    
                    # Service account
                    if service.template and hasattr(service.template, 'service_account'):
                        service_data["service_account"] = service.template.service_account
                    
                    # Timeout
                    if service.template and hasattr(service.template, 'timeout'):
                        service_data["timeout_seconds"] = int(service.template.timeout.seconds)
                
                # Template metadata
                if service.template and hasattr(service.template, 'annotations'):
                    template_metadata = {}
                    if service.template.annotations:
                        template_metadata["annotations"] = dict(service.template.annotations)
                    if hasattr(service.template, 'labels') and service.template.labels:
                        template_metadata["labels"] = dict(service.template.labels)
                    if template_metadata:
                        service_data["template_metadata"] = template_metadata
                
                # Traffic
                if hasattr(service, 'traffic') and service.traffic:
                    service_data["traffic"] = []
                    for traffic in service.traffic:
                        traffic_data = {"percent": traffic.percent}
                        if hasattr(traffic, 'revision') and traffic.revision:
                            traffic_data["revision_name"] = traffic.revision.split('/')[-1]
                        if hasattr(traffic, 'latest_revision'):
                            traffic_data["latest_revision"] = traffic.latest_revision
                        service_data["traffic"].append(traffic_data)
                
                # Service metadata
                metadata = {}
                if hasattr(service, 'annotations') and service.annotations:
                    metadata["annotations"] = dict(service.annotations)
                if hasattr(service, 'labels') and service.labels:
                    metadata["labels"] = dict(service.labels)
                if metadata:
                    service_data["metadata"] = metadata
                
                # Autogenerate revision name
                if hasattr(service, 'generation'):
                    service_data["autogenerate_revision_name"] = True
                
                print(f"DEBUG: APPENDING service {service_name} - Total now: {len(services) + 1}")
                services.append(service_data)
                    
            except exceptions.InvalidArgument:
                # Region doesn't support Cloud Run
                continue
            except Exception as e:
                if region:
                    # If specific region requested, raise the error
                    typer.echo(f"Error fetching Cloud Run services in {scan_region}: {str(e)}", err=True)
                    raise
                else:
                    # Skip region if scanning all
                    continue
        
        print(f"DEBUG: Found services in regions: {debug_regions}")
        print(f"DEBUG: Total services before deduplication: {len(services)}")
        
        # NUCLEAR OPTION: Force deduplication by service name at the very end
        unique_services = {}
        for service in services:
            service_name = service.get('name', 'unknown')
            if service_name not in unique_services:
                unique_services[service_name] = service
        
        final_services = list(unique_services.values())
        print(f"DEBUG: Total FINAL services after nuclear dedup: {len(final_services)}")
        return final_services
    
    # Use safe operation wrapper
    return safe_gcp_operation(
        _scan_cloud_run, 
        "Cloud Run API", 
        project_id
    )

@app.command("scan")
def scan_cloud_run_services_command(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    region: Optional[str] = typer.Option(None, "--region", "-r", help="GCP region to scan.")
):
    """Scans GCP Cloud Run services and generates Terraform code."""
    if not project_id:
        typer.echo("Error: Project ID is required. Set GCP_PROJECT_ID or use --project-id", err=True)
        raise typer.Exit(code=1)
    
    typer.echo(f"Scanning for Cloud Run services in project '{project_id}'...")
    if region:
        typer.echo(f"Filtering by region: {region}")
    
    services_data = get_cloud_run_services_data(project_id, region)
    
    if not services_data:
        typer.echo("No Cloud Run services found.")
        return
    
    # Generate Terraform files
    output_file = output_dir / "gcp_cloud_run_service.tf"
    generate_tf(services_data, "gcp_cloud_run_service", output_file, provider="gcp", project_id=project_id)
    
    # Generate import file and print message only if we have services
    if services_data:
        typer.echo(f"Generated Terraform for {len(services_data)} Cloud Run services -> {output_file}")
        imports = []
        for service in services_data:
            imports.append({
                "resource_type": "google_cloud_run_service",
                "resource_name": service['name_sanitized'],
                "resource_id": service['name']
            })
        generate_imports_file(
            "gcp_cloud_run_service",
            services_data,
            "import_id",
            output_dir,
            provider="gcp"
        )

@app.command("list")
def list_cloud_run_services(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import file")
):
    """List all GCP Cloud Run services previously generated."""
    ImportManager(output_dir, "gcp_cloud_run_service").list_all()

@app.command("import")
def import_cloud_run_service(
    service_name: str = typer.Argument(..., help="Cloud Run service name to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory with import file")
):
    """Run terraform import for a specific Cloud Run service."""
    ImportManager(output_dir, "gcp_cloud_run_service").find_and_import(service_name)

# Scan function for cross-scan registry
def scan_cloud_run_services(
    output_dir: Path,
    project_id: str = None,
    region: str = None,
    zone: str = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP Cloud Run services in project {project_id}")
    
    services_data = get_cloud_run_services_data(project_id, region)
    
    if services_data:
        print(f"DEBUG: About to generate_tf with {len(services_data)} services")
        for i, svc in enumerate(services_data):
            print(f"DEBUG: Service {i+1}: {svc.get('name', 'UNKNOWN')}")
        output_file = output_dir / "gcp_cloud_run_service.tf"
        generate_tf(services_data, "gcp_cloud_run_service", output_file, provider="gcp", project_id=project_id)
        
        generate_imports_file(
            "gcp_cloud_run_service",
            services_data,
            "import_id",
            output_dir,
            provider="gcp"
        )
        
        typer.echo(f"[Cross-scan] Generated Terraform for {len(services_data)} Cloud Run services")