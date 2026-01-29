from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from google.cloud import dns
from google.api_core.exceptions import GoogleAPIError


def _process_managed_zone_data(zone: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP managed zone data for Terraform generation."""
    zone_data = {
        'name': zone.name,
        'dns_name': zone.dns_name,
        'description': zone.description,
        'visibility': zone.visibility,
        'project': project_id,
        'name_servers': list(zone.name_servers) if zone.name_servers else [],
        'creation_time': zone.creation_time
    }
    
    # Extract DNSSEC configuration if available
    if hasattr(zone, 'dnssec_config') and zone.dnssec_config:
        zone_data['dnssec_config'] = {
            'state': zone.dnssec_config.state,
            'kind': zone.dnssec_config.kind,
            'non_existence': zone.dnssec_config.non_existence if hasattr(zone.dnssec_config, 'non_existence') else None
        }
    
    # Extract labels if available
    if hasattr(zone, 'labels') and zone.labels:
        zone_data['labels'] = dict(zone.labels)
    
    # Extract forwarding config for private zones
    if hasattr(zone, 'forwarding_config') and zone.forwarding_config:
        zone_data['forwarding_config'] = {
            'target_name_servers': []
        }
        for server in zone.forwarding_config.target_name_servers:
            zone_data['forwarding_config']['target_name_servers'].append({
                'ipv4_address': server.ipv4_address,
                'forwarding_path': server.forwarding_path if hasattr(server, 'forwarding_path') else None
            })
    
    # Extract private visibility config
    if hasattr(zone, 'private_visibility_config') and zone.private_visibility_config:
        zone_data['private_visibility_config'] = {
            'networks': []
        }
        for network in zone.private_visibility_config.networks:
            zone_data['private_visibility_config']['networks'].append({
                'network_url': network.network_url
            })
    
    return zone_data


def get_managed_zone_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Managed Zone data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of managed zone data dictionaries
    """
    credentials, default_project = get_gcp_credentials()
    project_id = project_id or default_project
    
    client = dns.Client(project=project_id, credentials=credentials)
    zones_data = []
    
    try:
        # List managed zones for the project
        for zone in client.list_zones():
            zone_data = _process_managed_zone_data(zone, project_id)
            zones_data.append(zone_data)
                
    except GoogleAPIError as e:
        print(f"Error fetching GCP managed zones: {e}")
        
    return zones_data


def scan_managed_zones(output_dir: Path, project_id: Optional[str] = None):
    """
    Scan GCP managed zones and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
    """
    zones = get_managed_zone_data(project_id)
    
    if not zones:
        print("No managed zones found.")
        return
        
    output_file = output_dir / "gcp_dns_managed_zones.tf"
    generate_tf(zones, "gcp_dns_managed_zones", output_file)
    print(f"Generated Terraform for {len(zones)} GCP Managed Zones -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_dns_managed_zones", 
        zones, 
        remote_resource_id_key="name",
        output_dir=output_dir, provider="gcp"
    )


def list_managed_zones(output_dir: Path):
    """List all imported GCP managed zones."""
    ImportManager(output_dir, "gcp_dns_managed_zones").list_all()


def import_managed_zone(zone_name: str, output_dir: Path):
    """Import a specific GCP managed zone."""
    ImportManager(output_dir, "gcp_dns_managed_zones").find_and_import(zone_name)