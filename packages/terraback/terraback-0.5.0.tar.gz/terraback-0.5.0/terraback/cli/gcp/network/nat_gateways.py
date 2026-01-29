# terraback/cli/gcp/network/nat_gateways.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="nat-gateway", help="Scan and import GCP Cloud NAT gateways.")

def get_nat_gateway_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch Cloud NAT gateway data from GCP."""
    client = compute_v1.RoutersClient()
    nat_gateways = []
    
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
            
            routers = client.list(request=request)
            
            for router in routers:
                if hasattr(router, 'nats') and router.nats:
                    for nat in router.nats:
                        nat_data = {
                            "name": nat.name,
                            "id": f"{project_id}/{region_name}/{router.name}/{nat.name}",
                            "project": project_id,
                            "region": region_name,
                            "router": router.name,
                            
                            # NAT configuration
                            "nat_ip_allocate_option": nat.nat_ip_allocate_option if hasattr(nat, 'nat_ip_allocate_option') else "AUTO_ONLY",
                            "source_subnetwork_ip_ranges_to_nat": nat.source_subnetwork_ip_ranges_to_nat if hasattr(nat, 'source_subnetwork_ip_ranges_to_nat') else "ALL_SUBNETWORKS_ALL_IP_RANGES",
                            "nat_ips": list(nat.nat_ips) if hasattr(nat, 'nat_ips') and nat.nat_ips else [],
                            
                            # Subnetwork configurations
                            "subnetworks": [],
                            
                            # Logging
                            "enable_endpoint_independent_mapping": nat.enable_endpoint_independent_mapping if hasattr(nat, 'enable_endpoint_independent_mapping') else True,
                            "icmp_idle_timeout_sec": nat.icmp_idle_timeout_sec if hasattr(nat, 'icmp_idle_timeout_sec') else 30,
                            "tcp_established_idle_timeout_sec": nat.tcp_established_idle_timeout_sec if hasattr(nat, 'tcp_established_idle_timeout_sec') else 1200,
                            "tcp_transitory_idle_timeout_sec": nat.tcp_transitory_idle_timeout_sec if hasattr(nat, 'tcp_transitory_idle_timeout_sec') else 30,
                            "udp_idle_timeout_sec": nat.udp_idle_timeout_sec if hasattr(nat, 'udp_idle_timeout_sec') else 30,
                            
                            # Auto scaling
                            "min_ports_per_vm": nat.min_ports_per_vm if hasattr(nat, 'min_ports_per_vm') else 64,
                            "max_ports_per_vm": nat.max_ports_per_vm if hasattr(nat, 'max_ports_per_vm') else 65536,
                            
                            # For resource naming
                            "name_sanitized": f"{router.name}_{nat.name}".replace('-', '_').lower(),
                            "router_name_sanitized": router.name.replace('-', '_').lower(),
                        }
                        
                        # Process subnetwork configurations
                        if hasattr(nat, 'subnetworks') and nat.subnetworks:
                            for subnet_config in nat.subnetworks:
                                subnetwork_data = {
                                    "name": subnet_config.name.split('/')[-1] if hasattr(subnet_config, 'name') else None,
                                    "source_ip_ranges_to_nat": list(subnet_config.source_ip_ranges_to_nat) if hasattr(subnet_config, 'source_ip_ranges_to_nat') and subnet_config.source_ip_ranges_to_nat else ["ALL_IP_RANGES"],
                                    "secondary_ip_range_names": list(subnet_config.secondary_ip_range_names) if hasattr(subnet_config, 'secondary_ip_range_names') and subnet_config.secondary_ip_range_names else []
                                }
                                nat_data["subnetworks"].append(subnetwork_data)
                        
                        # Logging configuration
                        if hasattr(nat, 'log_config') and nat.log_config:
                            nat_data["log_config"] = {
                                "enable": nat.log_config.enable if hasattr(nat.log_config, 'enable') else False,
                                "filter": nat.log_config.filter if hasattr(nat.log_config, 'filter') else "ALL"
                            }
                        
                        nat_gateways.append(nat_data)
    
    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching NAT gateways: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return nat_gateways

@app.command("scan")
def scan_nat_gateways(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Cloud NAT gateways and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP NAT gateways with dependencies...")
        recursive_scan(
            "gcp_nat_gateway",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP NAT gateways in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Region: all regions")
        
        nat_data = get_nat_gateway_data(project_id, region)
        
        if not nat_data:
            typer.echo("No NAT gateways found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_nat_gateway.tf"
        generate_tf(nat_data, "gcp_nat_gateway", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(nat_data)} NAT gateways -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_nat_gateway",
            nat_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )

@app.command("list")
def list_nat_gateways(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP NAT gateway resources previously generated."""
    ImportManager(output_dir, "gcp_nat_gateway").list_all()

@app.command("import")
def import_nat_gateway(
    nat_id: str = typer.Argument(..., help="GCP NAT gateway ID (project/region/router/name)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP NAT gateway."""
    ImportManager(output_dir, "gcp_nat_gateway").find_and_import(nat_id)

# Scan function for cross-scan registry
def scan_gcp_nat_gateways(
    output_dir: Path,
    project_id: str = None,
    region: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP NAT gateways in project {project_id}")
    
    nat_data = get_nat_gateway_data(project_id, region)
    
    if nat_data:
        output_file = output_dir / "gcp_nat_gateway.tf"
        generate_tf(nat_data, "gcp_nat_gateway", output_file, provider="gcp")
        generate_imports_file(
            "gcp_nat_gateway",
            nat_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(nat_data)} GCP NAT gateways")