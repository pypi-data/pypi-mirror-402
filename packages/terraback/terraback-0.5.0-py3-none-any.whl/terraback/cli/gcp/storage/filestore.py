# terraback/cli/gcp/storage/filestore.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id, get_gcp_credentials

try:
    from google.cloud import filestore_v1
    FILESTORE_AVAILABLE = True
except ImportError:
    FILESTORE_AVAILABLE = False
    filestore_v1 = None
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="filestore", help="Scan and import GCP Filestore instances.")

def get_filestore_data(project_id: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch Filestore instance data from GCP."""
    if not FILESTORE_AVAILABLE:
        typer.echo("Warning: Filestore client library not available. Install with: pip install google-cloud-filestore", err=True)
        return []
    
    credentials = get_gcp_credentials()
    client = filestore_v1.CloudFilestoreManagerClient(credentials=credentials)
    filestore_instances = []
    
    try:
        if location:
            locations = [location]
        else:
            # Get all locations
            locations_request = filestore_v1.ListLocationsRequest(
                name=f"projects/{project_id}"
            )
            locations = [loc.location_id for loc in client.list_locations(request=locations_request)]
        
        for location_id in locations:
            parent = f"projects/{project_id}/locations/{location_id}"
            request = filestore_v1.ListInstancesRequest(parent=parent)
            
            try:
                instances = client.list_instances(request=request)
                
                for instance in instances:
                    instance_data = {
                        "name": instance.name.split('/')[-1],  # Extract instance name from full path
                        "id": instance.name,  # Full resource path
                        "project": project_id,
                        "location": location_id,
                        "tier": instance.tier.name if instance.tier else "BASIC_HDD",
                        "state": instance.state.name if instance.state else "CREATING",
                        
                        # File shares
                        "file_shares": [],
                        
                        # Network configuration
                        "networks": [],
                        
                        # Labels
                        "labels": dict(instance.labels) if instance.labels else {},
                        "description": instance.description if hasattr(instance, 'description') else "",
                        
                        # For resource naming
                        "name_sanitized": instance.name.split('/')[-1].replace('-', '_').lower(),
                        "create_time": instance.create_time.isoformat() if hasattr(instance, 'create_time') and instance.create_time else None,
                    }
                    
                    # Process file shares
                    if hasattr(instance, 'file_shares') and instance.file_shares:
                        for share_name, file_share in instance.file_shares.items():
                            share_data = {
                                "name": share_name,
                                "capacity_gb": file_share.capacity_gb if hasattr(file_share, 'capacity_gb') else None,
                                "source_backup": file_share.source_backup if hasattr(file_share, 'source_backup') else None,
                                "nfs_export_options": []
                            }
                            
                            # Process NFS export options
                            if hasattr(file_share, 'nfs_export_options') and file_share.nfs_export_options:
                                for export_option in file_share.nfs_export_options:
                                    option_data = {
                                        "ip_ranges": list(export_option.ip_ranges) if hasattr(export_option, 'ip_ranges') and export_option.ip_ranges else [],
                                        "access_mode": export_option.access_mode.name if hasattr(export_option, 'access_mode') else "READ_WRITE",
                                        "squash_mode": export_option.squash_mode.name if hasattr(export_option, 'squash_mode') else "NO_ROOT_SQUASH",
                                        "anon_uid": export_option.anon_uid if hasattr(export_option, 'anon_uid') else None,
                                        "anon_gid": export_option.anon_gid if hasattr(export_option, 'anon_gid') else None
                                    }
                                    share_data["nfs_export_options"].append(option_data)
                            
                            instance_data["file_shares"].append(share_data)
                    
                    # Process networks
                    if hasattr(instance, 'networks') and instance.networks:
                        for network in instance.networks:
                            network_data = {
                                "network": network.network.split('/')[-1] if hasattr(network, 'network') and network.network else None,
                                "modes": list(network.modes) if hasattr(network, 'modes') and network.modes else ["MODE_IPV4"],
                                "reserved_ip_range": network.reserved_ip_range if hasattr(network, 'reserved_ip_range') else None,
                                "connect_mode": network.connect_mode.name if hasattr(network, 'connect_mode') else "DIRECT_PEERING"
                            }
                            instance_data["networks"].append(network_data)
                    
                    filestore_instances.append(instance_data)
                    
            except exceptions.NotFound:
                # Location doesn't support Filestore
                continue
            
    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching Filestore instances: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return filestore_instances

@app.command("scan")
def scan_filestore(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    location: Optional[str] = typer.Option(None, "--location", "-l"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Filestore instances and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP Filestore instances with dependencies...")
        recursive_scan(
            "gcp_filestore",
            output_dir=output_dir,
            project_id=project_id,
            location=location
        )
    else:
        typer.echo(f"Scanning for GCP Filestore instances in project '{project_id}'...")
        if location:
            typer.echo(f"Location: {location}")
        else:
            typer.echo("Location: all locations")
        
        filestore_data = get_filestore_data(project_id, location)
        
        if not filestore_data:
            typer.echo("No Filestore instances found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_filestore.tf"
        generate_tf(filestore_data, "gcp_filestore", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(filestore_data)} Filestore instances -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_filestore",
            filestore_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )

@app.command("list")
def list_filestore(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP Filestore resources previously generated."""
    ImportManager(output_dir, "gcp_filestore").list_all()

@app.command("import")
def import_filestore(
    instance_id: str = typer.Argument(..., help="GCP Filestore instance ID"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP Filestore instance."""
    ImportManager(output_dir, "gcp_filestore").find_and_import(instance_id)

# Scan function for cross-scan registry
def scan_gcp_filestore(
    output_dir: Path,
    project_id: str = None,
    location: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP Filestore instances in project {project_id}")
    
    filestore_data = get_filestore_data(project_id, location)
    
    if filestore_data:
        output_file = output_dir / "gcp_filestore.tf"
        generate_tf(filestore_data, "gcp_filestore", output_file, provider="gcp")
        generate_imports_file(
            "gcp_filestore",
            filestore_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(filestore_data)} GCP Filestore instances")