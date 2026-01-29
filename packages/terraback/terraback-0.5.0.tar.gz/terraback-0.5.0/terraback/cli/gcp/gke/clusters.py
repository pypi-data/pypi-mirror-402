# terraback/cli/gcp/gke/clusters.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import container_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_gcp_credentials, get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="cluster", help="Scan and import GKE clusters.")

def get_gke_cluster_data(project_id: str, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch GKE cluster data from GCP."""
    session = get_gcp_credentials()
    client = container_v1.ClusterManagerClient(credentials=session)
    
    clusters = []
    
    try:
        # If location specified, scan just that location
        if location:
            locations_to_scan = [location]
        else:
            # List all locations (zones and regions)
            # For now, we'll scan common regions and zones
            locations_to_scan = [
                # Regional clusters
                "us-central1", "us-west1", "us-west2", "us-west3", "us-west4",
                "us-east1", "us-east4", "us-east5", "us-south1",
                "europe-west1", "europe-west2", "europe-west3", "europe-west4",
                "europe-west6", "europe-north1",
                "asia-east1", "asia-east2", "asia-northeast1", "asia-northeast2",
                "asia-northeast3", "asia-south1", "asia-southeast1", "asia-southeast2",
                # Add '-' to indicate we want to list all zones/regions
                "-"
            ]
        
        for loc in locations_to_scan:
            try:
                # Build parent path
                parent = f"projects/{project_id}/locations/{loc}"
                
                # List clusters in this location
                response = client.list_clusters(parent=parent)
                
                for cluster in response.clusters:
                    # Extract cluster data
                    cluster_data = {
                        "name": cluster.name,
                        "location": cluster.location if hasattr(cluster, 'location') else loc,
                        "project": project_id,
                        "name_sanitized": cluster.name.replace('-', '_').lower(),
                    }
                    
                    # Basic settings
                    if hasattr(cluster, 'description'):
                        cluster_data["description"] = cluster.description
                    
                    # Get the node version
                    if hasattr(cluster, 'current_node_version'):
                        cluster_data["node_version"] = cluster.current_node_version
                    
                    # Get master version
                    if hasattr(cluster, 'current_master_version'):
                        cluster_data["min_master_version"] = cluster.current_master_version
                    
                    # Network configuration
                    if hasattr(cluster, 'network'):
                        cluster_data["network"] = cluster.network.split('/')[-1]
                    if hasattr(cluster, 'subnetwork'):
                        cluster_data["subnetwork"] = cluster.subnetwork.split('/')[-1]
                    
                    # Cluster IPv4 CIDR
                    if hasattr(cluster, 'cluster_ipv4_cidr'):
                        cluster_data["cluster_ipv4_cidr"] = cluster.cluster_ipv4_cidr
                    
                    # Services IPv4 CIDR
                    if hasattr(cluster, 'services_ipv4_cidr'):
                        cluster_data["services_secondary_range_name"] = None  # Will be set from ip_allocation_policy
                    
                    # IP allocation policy
                    if hasattr(cluster, 'ip_allocation_policy') and cluster.ip_allocation_policy:
                        ip_policy = cluster.ip_allocation_policy
                        ip_allocation = {}
                        
                        if hasattr(ip_policy, 'cluster_secondary_range_name'):
                            ip_allocation["cluster_secondary_range_name"] = ip_policy.cluster_secondary_range_name
                        if hasattr(ip_policy, 'services_secondary_range_name'):
                            ip_allocation["services_secondary_range_name"] = ip_policy.services_secondary_range_name
                        if hasattr(ip_policy, 'cluster_ipv4_cidr_block'):
                            ip_allocation["cluster_ipv4_cidr_block"] = ip_policy.cluster_ipv4_cidr_block
                        if hasattr(ip_policy, 'services_ipv4_cidr_block'):
                            ip_allocation["services_ipv4_cidr_block"] = ip_policy.services_ipv4_cidr_block
                        
                        if ip_allocation:
                            cluster_data["ip_allocation_policy"] = ip_allocation
                    
                    # Master auth configuration
                    if hasattr(cluster, 'master_auth') and cluster.master_auth:
                        master_auth = {}
                        if hasattr(cluster.master_auth, 'client_certificate_config'):
                            master_auth["client_certificate_config"] = {
                                "issue_client_certificate": cluster.master_auth.client_certificate_config.issue_client_certificate
                            }
                        if master_auth:
                            cluster_data["master_auth"] = master_auth
                    
                    # Master authorized networks
                    if hasattr(cluster, 'master_authorized_networks_config') and cluster.master_authorized_networks_config:
                        if cluster.master_authorized_networks_config.enabled:
                            auth_networks = []
                            for network in cluster.master_authorized_networks_config.cidr_blocks:
                                auth_networks.append({
                                    "cidr_block": network.cidr_block,
                                    "display_name": network.display_name if hasattr(network, 'display_name') else ""
                                })
                            if auth_networks:
                                cluster_data["master_authorized_networks_config"] = {
                                    "cidr_blocks": auth_networks
                                }
                    
                    # Private cluster config
                    if hasattr(cluster, 'private_cluster_config') and cluster.private_cluster_config:
                        private_config = cluster.private_cluster_config
                        private_data = {}
                        
                        if hasattr(private_config, 'enable_private_nodes'):
                            private_data["enable_private_nodes"] = private_config.enable_private_nodes
                        if hasattr(private_config, 'enable_private_endpoint'):
                            private_data["enable_private_endpoint"] = private_config.enable_private_endpoint
                        if hasattr(private_config, 'master_ipv4_cidr_block'):
                            private_data["master_ipv4_cidr_block"] = private_config.master_ipv4_cidr_block
                        if hasattr(private_config, 'master_global_access_config'):
                            private_data["master_global_access_config"] = {
                                "enabled": private_config.master_global_access_config.enabled
                            }
                        
                        if private_data:
                            cluster_data["private_cluster_config"] = private_data
                    
                    # Workload identity config
                    if hasattr(cluster, 'workload_identity_config') and cluster.workload_identity_config:
                        if hasattr(cluster.workload_identity_config, 'workload_pool'):
                            cluster_data["workload_identity_config"] = {
                                "workload_pool": cluster.workload_identity_config.workload_pool
                            }
                    
                    # Binary authorization
                    if hasattr(cluster, 'binary_authorization') and cluster.binary_authorization:
                        if hasattr(cluster.binary_authorization, 'enabled'):
                            cluster_data["binary_authorization"] = {
                                "enabled": cluster.binary_authorization.enabled,
                                "evaluation_mode": cluster.binary_authorization.evaluation_mode if hasattr(cluster.binary_authorization, 'evaluation_mode') else "DISABLED"
                            }
                    
                    # Addons config
                    if hasattr(cluster, 'addons_config') and cluster.addons_config:
                        addons = cluster.addons_config
                        addons_data = {}
                        
                        # HTTP load balancing
                        if hasattr(addons, 'http_load_balancing'):
                            addons_data["http_load_balancing"] = {
                                "disabled": addons.http_load_balancing.disabled
                            }
                        
                        # Horizontal pod autoscaling
                        if hasattr(addons, 'horizontal_pod_autoscaling'):
                            addons_data["horizontal_pod_autoscaling"] = {
                                "disabled": addons.horizontal_pod_autoscaling.disabled
                            }
                        
                        # Network policy config
                        if hasattr(addons, 'network_policy_config'):
                            addons_data["network_policy_config"] = {
                                "disabled": addons.network_policy_config.disabled
                            }
                        
                        # GCP filestore CSI driver
                        if hasattr(addons, 'gcp_filestore_csi_driver_config'):
                            addons_data["gcp_filestore_csi_driver_config"] = {
                                "enabled": addons.gcp_filestore_csi_driver_config.enabled
                            }
                        
                        # GKE backup agent
                        if hasattr(addons, 'gke_backup_agent_config'):
                            addons_data["gke_backup_agent_config"] = {
                                "enabled": addons.gke_backup_agent_config.enabled
                            }
                        
                        if addons_data:
                            cluster_data["addons_config"] = addons_data
                    
                    # Network policy
                    if hasattr(cluster, 'network_policy') and cluster.network_policy:
                        cluster_data["network_policy"] = {
                            "enabled": cluster.network_policy.enabled,
                            "provider": cluster.network_policy.provider.name if hasattr(cluster.network_policy, 'provider') else "CALICO"
                        }
                    
                    # Maintenance policy
                    if hasattr(cluster, 'maintenance_policy') and cluster.maintenance_policy:
                        if hasattr(cluster.maintenance_policy, 'window') and cluster.maintenance_policy.window:
                            window = cluster.maintenance_policy.window
                            if hasattr(window, 'daily_maintenance_window') and window.daily_maintenance_window:
                                cluster_data["maintenance_policy"] = {
                                    "daily_maintenance_window": {
                                        "start_time": window.daily_maintenance_window.start_time
                                    }
                                }
                    
                    # Resource labels
                    if hasattr(cluster, 'resource_labels') and cluster.resource_labels:
                        cluster_data["resource_labels"] = dict(cluster.resource_labels)
                    
                    # Logging and monitoring config
                    if hasattr(cluster, 'logging_config') and cluster.logging_config:
                        if hasattr(cluster.logging_config, 'component_config'):
                            logging_components = []
                            for component in cluster.logging_config.component_config.enable_components:
                                logging_components.append(component.name)
                            if logging_components:
                                cluster_data["logging_service"] = "logging.googleapis.com/kubernetes"
                                cluster_data["cluster_telemetry"] = {
                                    "type": "ENABLED"
                                }
                    
                    if hasattr(cluster, 'monitoring_config') and cluster.monitoring_config:
                        if hasattr(cluster.monitoring_config, 'component_config'):
                            monitoring_components = []
                            for component in cluster.monitoring_config.component_config.enable_components:
                                monitoring_components.append(component.name)
                            if monitoring_components:
                                cluster_data["monitoring_service"] = "monitoring.googleapis.com/kubernetes"
                    
                    # Default max pods per node
                    if hasattr(cluster, 'default_max_pods_constraint') and cluster.default_max_pods_constraint:
                        cluster_data["default_max_pods_per_node"] = cluster.default_max_pods_constraint.max_pods_per_node
                    
                    # Enable features
                    cluster_data["remove_default_node_pool"] = True  # Best practice
                    cluster_data["initial_node_count"] = 1  # Required when remove_default_node_pool is true
                    
                    clusters.append(cluster_data)
                    
            except exceptions.NotFound:
                # Location doesn't exist or has no clusters
                continue
            except exceptions.InvalidArgument:
                # Invalid location format
                continue
            except Exception as e:
                if location:
                    # If specific location requested, raise the error
                    typer.echo(f"Error fetching GKE clusters in location {loc}: {str(e)}", err=True)
                    raise
                else:
                    # Skip location if scanning all
                    continue
                    
    except Exception as e:
        typer.echo(f"Error fetching GKE clusters: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return clusters

@app.command("scan")
def scan_gke_clusters(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", help="GCP Project ID.", envvar="GCP_PROJECT_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="GCP location (region or zone) to scan"),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan dependencies")
):
    """Scans GKE clusters and generates Terraform code."""
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GCP_PROJECT_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        typer.echo("Scanning GKE clusters with dependencies...")
        recursive_scan("gcp_gke_cluster", output_dir=output_dir, project_id=project_id, location=location)
    else:
        if location:
            typer.echo(f"Scanning for GKE clusters in location '{location}'...")
        else:
            typer.echo(f"Scanning for GKE clusters in all locations in project '{project_id}'...")
        
        clusters_data = get_gke_cluster_data(project_id, location)
        
        if not clusters_data:
            typer.echo("No GKE clusters found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_gke_cluster.tf"
        generate_tf(clusters_data, "gcp_gke_cluster", output_file, provider="gcp", project_id=project_id)
        typer.echo(f"Generated Terraform for {len(clusters_data)} GKE clusters -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_gke_cluster",
            clusters_data,
            output_dir=output_dir, provider="gcp"
        )

# Scan function for cross-scan registry
def scan_gcp_gke_clusters(
    output_dir: Path, 
    project_id: Optional[str] = None,
    location: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GKE clusters in project {project_id}")
    
    clusters_data = get_gke_cluster_data(project_id, location)
    
    if clusters_data:
        output_file = output_dir / "gcp_gke_cluster.tf"
        generate_tf(clusters_data, "gcp_gke_cluster", output_file, provider="gcp", project_id=project_id)
        
        generate_imports_file(
            "gcp_gke_cluster",
            clusters_data,
            output_dir=output_dir, provider="gcp"
        )
        
        typer.echo(f"[Cross-scan] Generated Terraform for {len(clusters_data)} GKE clusters")

@app.command("list")
def list_gke_clusters(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all GKE cluster resources previously generated."""
    ImportManager(output_dir, "gcp_gke_cluster").list_all()

@app.command("import")
def import_gke_cluster(
    cluster_id: str = typer.Argument(..., help="GKE cluster ID"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GKE cluster."""
    ImportManager(output_dir, "gcp_gke_cluster").find_and_import(cluster_id)
