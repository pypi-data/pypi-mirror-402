# terraback/cli/gcp/network/routers.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="router", help="Scan and import GCP Cloud routers.")

def get_router_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch Cloud router data from GCP."""
    client = compute_v1.RoutersClient()
    routers = []
    
    try:
        if region:
            regions = [region]
        else:
            # Get all regions
            regions_client = compute_v1.RegionsClient()
            regions_request = compute_v1.ListRegionsRequest(project=project_id)
            regions = [r.name for r in regions_client.list(request=regions_request)]
        
        for region_name in regions:
            request = compute_v1.ListRoutersRequest(
                project=project_id,
                region=region_name
            )
            
            router_list = client.list(request=request)
            
            for router in router_list:
                router_data = {
                    "name": router.name,
                    "id": f"{project_id}/{region_name}/{router.name}",
                    "project": project_id,
                    "region": region_name,
                    "network": router.network.split('/')[-1] if router.network else None,
                    "description": router.description if hasattr(router, 'description') else "",
                    
                    # BGP configuration
                    "bgp": None,
                    
                    # For resource naming
                    "name_sanitized": router.name.replace('-', '_').lower(),
                    "creation_timestamp": router.creation_timestamp if hasattr(router, 'creation_timestamp') else None,
                }
                
                # Process BGP configuration
                if hasattr(router, 'bgp') and router.bgp:
                    bgp_data = {
                        "asn": router.bgp.asn if hasattr(router.bgp, 'asn') else None,
                        "advertise_mode": router.bgp.advertise_mode if hasattr(router.bgp, 'advertise_mode') else "DEFAULT",
                        "advertised_groups": list(router.bgp.advertised_groups) if hasattr(router.bgp, 'advertised_groups') and router.bgp.advertised_groups else [],
                        "advertised_ip_ranges": []
                    }
                    
                    # Process advertised IP ranges
                    if hasattr(router.bgp, 'advertised_ip_ranges') and router.bgp.advertised_ip_ranges:
                        for ip_range in router.bgp.advertised_ip_ranges:
                            bgp_data["advertised_ip_ranges"].append({
                                "range": ip_range.range if hasattr(ip_range, 'range') else None,
                                "description": ip_range.description if hasattr(ip_range, 'description') else ""
                            })
                    
                    router_data["bgp"] = bgp_data
                
                routers.append(router_data)
    
    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching routers: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return routers

@app.command("scan")
def scan_routers(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Cloud routers and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP routers with dependencies...")
        recursive_scan(
            "gcp_router",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP routers in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Region: all regions")
        
        router_data = get_router_data(project_id, region)
        
        if not router_data:
            typer.echo("No routers found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_router.tf"
        generate_tf(router_data, "gcp_router", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(router_data)} routers -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_router",
            router_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )

@app.command("list")
def list_routers(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP router resources previously generated."""
    ImportManager(output_dir, "gcp_router").list_all()

@app.command("import")
def import_router(
    router_id: str = typer.Argument(..., help="GCP router ID (project/region/name)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP router."""
    ImportManager(output_dir, "gcp_router").find_and_import(router_id)

# Scan function for cross-scan registry
def scan_gcp_routers(
    output_dir: Path,
    project_id: str = None,
    region: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP routers in project {project_id}")
    
    router_data = get_router_data(project_id, region)
    
    if router_data:
        output_file = output_dir / "gcp_router.tf"
        generate_tf(router_data, "gcp_router", output_file, provider="gcp")
        generate_imports_file(
            "gcp_router",
            router_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(router_data)} GCP routers")