# terraback/cli/gcp/gke/node_pools.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import container_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="node-pool", help="Scan and import GKE node pools.")

def get_gke_node_pool_data(project_id: str, region: Optional[str] = None, zone: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch GKE node pool data from GCP."""
    node_pools = []

    try:
        client = container_v1.ClusterManagerClient()

        # Determine locations to scan
        locations = []
        if region:
            locations = [region]
        elif zone:
            locations = [zone]
        else:
            # Get all regions and zones if none specified
            typer.echo("Scanning GKE node pools across all regions...")
            locations = ["-"]  # Use "-" to scan all locations

        for location in locations:
            try:
                # List clusters first, then get node pools for each cluster
                parent = f"projects/{project_id}/locations/{location}"

                clusters_response = client.list_clusters(parent=parent)

                for cluster in clusters_response.clusters:
                    cluster_location = cluster.location
                    cluster_name = cluster.name

                    typer.echo(f"Scanning node pools for cluster '{cluster_name}' in {cluster_location}...")

                    # Get node pools for this cluster
                    for node_pool in cluster.node_pools:
                        node_pool_data = {
                            'id': f"{project_id}/{cluster_location}/{cluster_name}/{node_pool.name}",
                            'name': node_pool.name,
                            'name_sanitized': node_pool.name.replace('-', '_'),
                            'project': project_id,
                            'location': cluster_location,
                            'cluster': cluster_name,
                            'terraform_type': 'google_container_node_pool',

                            # Core node pool properties
                            'node_count': getattr(node_pool, 'initial_node_count', 0),
                            'version': getattr(node_pool, 'version', ''),
                            'status': getattr(node_pool, 'status', ''),

                            # Node configuration
                            'node_config': {
                                'machine_type': getattr(node_pool.config, 'machine_type', '')
                                    if hasattr(node_pool, 'config') and node_pool.config else '',
                                'disk_size_gb': getattr(node_pool.config, 'disk_size_gb', 0)
                                    if hasattr(node_pool, 'config') and node_pool.config else 0,
                                'disk_type': getattr(node_pool.config, 'disk_type', '')
                                    if hasattr(node_pool, 'config') and node_pool.config else '',
                                'local_ssd_count': getattr(node_pool.config, 'local_ssd_count', 0)
                                    if hasattr(node_pool, 'config') and node_pool.config else 0,
                                'preemptible': getattr(node_pool.config, 'preemptible', False)
                                    if hasattr(node_pool, 'config') and node_pool.config else False,
                                'spot': getattr(node_pool.config, 'spot', False)
                                    if hasattr(node_pool, 'config') and node_pool.config else False,
                                'image_type': getattr(node_pool.config, 'image_type', '')
                                    if hasattr(node_pool, 'config') and node_pool.config else '',
                                'labels': dict(getattr(node_pool.config, 'labels', {}))
                                    if hasattr(node_pool, 'config') and node_pool.config else {},
                                'tags': list(getattr(node_pool.config, 'tags', []))
                                    if hasattr(node_pool, 'config') and node_pool.config else [],
                                'service_account': getattr(node_pool.config, 'service_account', '')
                                    if hasattr(node_pool, 'config') and node_pool.config else '',
                                'oauth_scopes': list(getattr(node_pool.config, 'oauth_scopes', []))
                                    if hasattr(node_pool, 'config') and node_pool.config else [],
                                'min_cpu_platform': getattr(node_pool.config, 'min_cpu_platform', '')
                                    if hasattr(node_pool, 'config') and node_pool.config else ''
                            } if hasattr(node_pool, 'config') and node_pool.config else {},

                            # Autoscaling configuration
                            'autoscaling': {
                                'enabled': getattr(node_pool.autoscaling, 'enabled', False)
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else False,
                                'min_node_count': getattr(node_pool.autoscaling, 'min_node_count', 0)
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else 0,
                                'max_node_count': getattr(node_pool.autoscaling, 'max_node_count', 0)
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else 0,
                                'total_min_node_count': getattr(node_pool.autoscaling, 'total_min_node_count', 0)
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else 0,
                                'total_max_node_count': getattr(node_pool.autoscaling, 'total_max_node_count', 0)
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else 0,
                                'location_policy': getattr(node_pool.autoscaling, 'location_policy', '')
                                    if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else ''
                            } if hasattr(node_pool, 'autoscaling') and node_pool.autoscaling else None,

                            # Management configuration
                            'management': {
                                'auto_upgrade': getattr(node_pool.management, 'auto_upgrade', False)
                                    if hasattr(node_pool, 'management') and node_pool.management else False,
                                'auto_repair': getattr(node_pool.management, 'auto_repair', False)
                                    if hasattr(node_pool, 'management') and node_pool.management else False,
                                'upgrade_options': getattr(node_pool.management, 'upgrade_options', None)
                                    if hasattr(node_pool, 'management') and node_pool.management else None
                            } if hasattr(node_pool, 'management') and node_pool.management else None,

                            # Network configuration
                            'network_config': {
                                'pod_range': getattr(node_pool.network_config, 'pod_range', '')
                                    if hasattr(node_pool, 'network_config') and node_pool.network_config else '',
                                'pod_ipv4_cidr_block': getattr(node_pool.network_config, 'pod_ipv4_cidr_block', '')
                                    if hasattr(node_pool, 'network_config') and node_pool.network_config else '',
                                'enable_private_nodes': getattr(node_pool.network_config, 'enable_private_nodes', False)
                                    if hasattr(node_pool, 'network_config') and node_pool.network_config else False
                            } if hasattr(node_pool, 'network_config') and node_pool.network_config else None,

                            # Upgrade settings
                            'upgrade_settings': {
                                'max_surge': getattr(node_pool.upgrade_settings, 'max_surge', 0)
                                    if hasattr(node_pool, 'upgrade_settings') and node_pool.upgrade_settings else 0,
                                'max_unavailable': getattr(node_pool.upgrade_settings, 'max_unavailable', 0)
                                    if hasattr(node_pool, 'upgrade_settings') and node_pool.upgrade_settings else 0,
                                'strategy': getattr(node_pool.upgrade_settings, 'strategy', '')
                                    if hasattr(node_pool, 'upgrade_settings') and node_pool.upgrade_settings else ''
                            } if hasattr(node_pool, 'upgrade_settings') and node_pool.upgrade_settings else None,

                            # Placement policy
                            'placement_policy': {
                                'type_': getattr(node_pool.placement_policy, 'type_', '')
                                    if hasattr(node_pool, 'placement_policy') and node_pool.placement_policy else '',
                                'policy_name': getattr(node_pool.placement_policy, 'policy_name', '')
                                    if hasattr(node_pool, 'placement_policy') and node_pool.placement_policy else ''
                            } if hasattr(node_pool, 'placement_policy') and node_pool.placement_policy else None,

                            # Node locations
                            'locations': list(getattr(node_pool, 'locations', [])),

                            # Lifecycle information
                            'status_message': getattr(node_pool, 'status_message', ''),
                            'max_pods_constraint': {
                                'max_pods_per_node': getattr(node_pool.max_pods_constraint, 'max_pods_per_node', 0)
                                    if hasattr(node_pool, 'max_pods_constraint') and node_pool.max_pods_constraint else 0
                            } if hasattr(node_pool, 'max_pods_constraint') and node_pool.max_pods_constraint else None,

                            # Conditions
                            'conditions': [
                                {
                                    'code': condition.code,
                                    'message': condition.message,
                                    'canonical_code': condition.canonical_code
                                } for condition in getattr(node_pool, 'conditions', [])
                            ],

                            # Raw data for templates
                            'raw': node_pool
                        }
                        node_pools.append(node_pool_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan node pools in location {location}: {str(e)}", err=True)

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching GKE node pools: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return node_pools

@app.command("scan")
def scan_gke_node_pools(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GKE node pools and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        typer.echo("Scanning GKE node pools with dependencies...")
        recursive_scan(
            "gcp_gke_node_pool",
            output_dir=output_dir,
            project_id=project_id,
            region=region,
            zone=zone
        )
    else:
        location_str = region or zone or "all locations"
        typer.echo(f"Scanning GKE node pools in project '{project_id}' ({location_str})...")

        node_pool_data = get_gke_node_pool_data(project_id, region, zone)

        if not node_pool_data:
            typer.echo("No GKE node pools found.")
            return

        # Generate Terraform files
        output_file = output_dir / "gcp_gke_node_pool.tf"
        generate_tf(node_pool_data, "gcp_gke_node_pool", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(node_pool_data)} node pools -> {output_file}")

        # Generate import file
        generate_imports_file(
            "gcp_gke_node_pool",
            node_pool_data,
            remote_resource_id_key="id",
            output_dir=output_dir,
            provider="gcp"
        )

@app.command("list")
def list_gke_node_pools(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all GKE node pool resources previously generated."""
    ImportManager(output_dir, "gcp_gke_node_pool").list_all()

@app.command("import")
def import_gke_node_pool(
    node_pool_id: str = typer.Argument(..., help="GKE node pool ID (project/location/cluster/node_pool)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GKE node pool."""
    ImportManager(output_dir, "gcp_gke_node_pool").find_and_import(node_pool_id)

# Scan function for cross-scan registry
def scan_gcp_gke_node_pools(
    output_dir: Path,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    zone: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"[Cross-scan] Scanning GKE node pools in project {project_id}")

    node_pool_data = get_gke_node_pool_data(project_id, region, zone)

    if node_pool_data:
        output_file = output_dir / "gcp_gke_node_pool.tf"
        generate_tf(node_pool_data, "gcp_gke_node_pool", output_file, provider="gcp")
        generate_imports_file(
            "gcp_gke_node_pool",
            node_pool_data,
            remote_resource_id_key="id",
            output_dir=output_dir,
            provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(node_pool_data)} GKE node pools")