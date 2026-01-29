"""Azure Kubernetes Service (AKS) scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from terraback.core.license import require_professional

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="aks", help="Scan and import Azure Kubernetes Service clusters.")

@require_professional
def scan_aks_clusters(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None  # Accept but ignore location parameter for compatibility
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Kubernetes Service (AKS) clusters and generate Terraform configurations.
    
    This function retrieves all AKS clusters from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of AKS cluster resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    aks_client = get_azure_client('ContainerServiceClient', subscription_id)
    clusters: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure Kubernetes Service clusters...")
    print("Scanning for AKS Clusters...")
    
    # List all AKS clusters with error handling
    @safe_azure_operation("list AKS clusters", default_return=[])
    def list_clusters():
        if resource_group_name:
            return list(aks_client.managed_clusters.list_by_resource_group(resource_group_name))
        else:
            return list(aks_client.managed_clusters.list())
    
    cluster_list = list_clusters()
    
    # Process each cluster
    for cluster in cluster_list:
        cluster_dict = format_resource_dict(cluster, 'kubernetes_cluster')
        
        # Format cluster properties
        _format_default_node_pool(cluster_dict, cluster)
        _format_identity(cluster_dict, cluster)
        _format_network_profile(cluster_dict, cluster)
        _format_addon_profiles(cluster_dict, cluster)
        _format_auto_scaler_profile(cluster_dict, cluster)
        _format_azure_ad_profile(cluster_dict, cluster)
        
        clusters.append(cluster_dict)
        logger.debug(f"Processed AKS cluster: {cluster.name}")    # Process resources before generation
    clusters = process_resources(clusters, "azure_kubernetes_cluster")
    

    
    # Generate Terraform files
    if clusters:
        generate_tf_auto(clusters, "azure_kubernetes_cluster", output_dir)
        
        generate_imports_file(
            "azure_kubernetes_cluster",
            clusters,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No AKS Clusters found.")
        logger.info("No AKS Clusters found.")
    
    return clusters

def _format_default_node_pool(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format default node pool configuration."""
    if not hasattr(cluster, 'agent_pool_profiles') or not cluster.agent_pool_profiles:
        return
        
    default_pool = cluster.agent_pool_profiles[0]
    cluster_dict['default_node_pool_formatted'] = {
        'name': default_pool.name,
        'node_count': default_pool.count,
        'vm_size': default_pool.vm_size,
        'os_disk_size_gb': default_pool.os_disk_size_gb,
        'vnet_subnet_id': default_pool.vnet_subnet_id,
        'max_pods': default_pool.max_pods,
        'os_type': default_pool.os_type,
        'enable_auto_scaling': default_pool.enable_auto_scaling,
        'min_count': default_pool.min_count,
        'max_count': default_pool.max_count,
        'availability_zones': default_pool.availability_zones,
        'enable_node_public_ip': default_pool.enable_node_public_ip,
        'node_labels': default_pool.node_labels,
        'node_taints': default_pool.node_taints
    }


def _format_identity(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format service principal or managed identity."""
    if hasattr(cluster, 'service_principal_profile') and cluster.service_principal_profile:
        cluster_dict['service_principal_formatted'] = {
            'client_id': cluster.service_principal_profile.client_id,
            'client_secret': 'REDACTED'  # Don't expose secrets
        }
    
    if hasattr(cluster, 'identity') and cluster.identity:
        cluster_dict['identity_formatted'] = {
            'type': cluster.identity.type,
            'principal_id': cluster.identity.principal_id,
            'tenant_id': cluster.identity.tenant_id
        }


def _format_network_profile(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format network profile configuration."""
    if not hasattr(cluster, 'network_profile') or not cluster.network_profile:
        return
        
    np = cluster.network_profile
    cluster_dict['network_profile_formatted'] = {
        'network_plugin': np.network_plugin,
        'network_policy': np.network_policy,
        'dns_service_ip': np.dns_service_ip,
        'docker_bridge_cidr': np.docker_bridge_cidr,
        'pod_cidr': np.pod_cidr,
        'service_cidr': np.service_cidr,
        'load_balancer_sku': np.load_balancer_sku,
        'outbound_type': np.outbound_type
    }


def _format_addon_profiles(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format addon profiles."""
    if not hasattr(cluster, 'addon_profiles') or not cluster.addon_profiles:
        return
        
    cluster_dict['addon_profiles_formatted'] = {}
    for addon_name, addon_config in cluster.addon_profiles.items():
        if addon_config.enabled:
            cluster_dict['addon_profiles_formatted'][addon_name] = {
                'enabled': addon_config.enabled,
                'config': addon_config.config or {}
            }


def _format_auto_scaler_profile(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format auto scaler profile."""
    if not hasattr(cluster, 'auto_scaler_profile') or not cluster.auto_scaler_profile:
        return
        
    asp = cluster.auto_scaler_profile
    cluster_dict['auto_scaler_profile_formatted'] = {
        'balance_similar_node_groups': asp.balance_similar_node_groups,
        'expander': asp.expander,
        'max_graceful_termination_sec': asp.max_graceful_termination_sec,
        'max_node_provision_time': asp.max_node_provision_time,
        'ok_total_unready_count': asp.ok_total_unready_count,
        'max_total_unready_percentage': asp.max_total_unready_percentage,
        'new_pod_scale_up_delay': asp.new_pod_scale_up_delay,
        'scale_down_delay_after_add': asp.scale_down_delay_after_add,
        'scale_down_delay_after_delete': asp.scale_down_delay_after_delete,
        'scale_down_delay_after_failure': asp.scale_down_delay_after_failure,
        'scale_down_unneeded_time': asp.scale_down_unneeded_time,
        'scale_down_unready_time': asp.scale_down_unready_time,
        'scale_down_utilization_threshold': asp.scale_down_utilization_threshold,
        'skip_nodes_with_local_storage': asp.skip_nodes_with_local_storage,
        'skip_nodes_with_system_pods': asp.skip_nodes_with_system_pods
    }


def _format_azure_ad_profile(cluster_dict: Dict[str, Any], cluster: Any) -> None:
    """Format Azure AD/RBAC settings."""
    if not hasattr(cluster, 'aad_profile') or not cluster.aad_profile:
        return
        
    cluster_dict['azure_active_directory_role_based_access_control_formatted'] = {
        'managed': cluster.aad_profile.managed,
        'admin_group_object_ids': cluster.aad_profile.admin_group_object_i_ds,
        'tenant_id': cluster.aad_profile.tenant_id
    }


def scan_aks_node_pools(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for additional AKS node pools and generate Terraform configurations.
    
    This function retrieves all node pools (excluding default) from AKS clusters
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of AKS node pool resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    aks_client = get_azure_client('ContainerServiceClient', subscription_id)
    node_pools: List[Dict[str, Any]] = []
    
    logger.info("Scanning for AKS Node Pools...")
    print("Scanning for AKS Node Pools...")
    
    # Get all clusters first
    clusters = scan_aks_clusters(Path("/tmp"), subscription_id, resource_group_name)
    
    # Process node pools for each cluster
    for cluster in clusters:
        node_pools_for_cluster = _get_node_pools_for_cluster(
            aks_client,
            cluster['resource_group_name'],
            cluster['name'],
            cluster['id'],
            cluster.get('default_node_pool_formatted', {}).get('name')
        )
        node_pools.extend(node_pools_for_cluster)
    
    # Generate Terraform files
    if node_pools:
        generate_tf_auto(node_pools, "azure_kubernetes_cluster_node_pool", output_dir)
        
        generate_imports_file(
            "azure_kubernetes_cluster_node_pool",
            node_pools,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No additional AKS Node Pools found.")
        logger.info("No additional AKS Node Pools found.")
    
    return node_pools

def _get_node_pools_for_cluster(
    aks_client: Any,
    resource_group: str,
    cluster_name: str,
    cluster_id: str,
    default_pool_name: Optional[str]
) -> List[Dict[str, Any]]:
    """Get all node pools for a specific cluster."""
    @safe_azure_operation(f"list node pools for {cluster_name}", default_return=[])
    def list_pools():
        pools = list(aks_client.agent_pools.list(
            resource_group_name=resource_group,
            resource_name=cluster_name
        ))
        
        result = []
        for pool in pools:
            # Skip the default node pool (already handled in cluster)
            if default_pool_name and pool.name == default_pool_name:
                continue
            
            pool_dict = format_resource_dict(pool, 'kubernetes_cluster_node_pool')
            
            # Override sanitized name to include cluster name
            pool_dict['name_sanitized'] = f"{cluster_name}_{pool.name}".replace('-', '_').replace('.', '_').lower()
            
            # Add cluster info
            pool_dict['kubernetes_cluster_id'] = cluster_id
            pool_dict['resource_group_name'] = resource_group
            
            # Format pool properties
            _format_node_pool_properties(pool_dict, pool)
            
            result.append(pool_dict)
        
        return result
    
    return list_pools()


def _format_node_pool_properties(pool_dict: Dict[str, Any], pool: Any) -> None:
    """Format node pool properties for Terraform."""
    pool_dict['node_count'] = pool.count
    pool_dict['vm_size'] = pool.vm_size
    pool_dict['os_disk_size_gb'] = pool.os_disk_size_gb
    pool_dict['vnet_subnet_id'] = pool.vnet_subnet_id
    pool_dict['max_pods'] = pool.max_pods
    pool_dict['os_type'] = pool.os_type
    pool_dict['enable_auto_scaling'] = pool.enable_auto_scaling
    pool_dict['min_count'] = pool.min_count
    pool_dict['max_count'] = pool.max_count
    pool_dict['availability_zones'] = pool.availability_zones
    pool_dict['enable_node_public_ip'] = pool.enable_node_public_ip
    pool_dict['node_labels'] = pool.node_labels
    pool_dict['node_taints'] = pool.node_taints
    pool_dict['mode'] = pool.mode
    pool_dict['orchestrator_version'] = pool.orchestrator_version


# CLI Commands
@app.command("scan-clusters")
def scan_aks_clusters_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure Kubernetes Service clusters and generates Terraform code."""
    typer.echo(f"Scanning for AKS clusters in subscription '{subscription_id}'...")
    
    try:
        scan_aks_clusters(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning AKS clusters: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("scan-node-pools")
def scan_aks_node_pools_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans additional AKS node pools and generates Terraform code."""
    typer.echo(f"Scanning for AKS node pools in subscription '{subscription_id}'...")
    
    try:
        scan_aks_node_pools(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning AKS node pools: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list-clusters")
def list_aks_clusters(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all AKS Cluster resources previously generated."""
    ImportManager(output_dir, "azure_kubernetes_cluster").list_all()


@app.command("import-cluster")
def import_aks_cluster(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the AKS cluster to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific AKS Cluster."""
    ImportManager(output_dir, "azure_kubernetes_cluster").find_and_import(resource_id)


@app.command("list-node-pools")
def list_aks_node_pools(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all AKS Node Pool resources previously generated."""
    ImportManager(output_dir, "azure_kubernetes_cluster_node_pool").list_all()


@app.command("import-node-pool")
def import_aks_node_pool(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the AKS node pool to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific AKS Node Pool."""
    ImportManager(output_dir, "azure_kubernetes_cluster_node_pool").find_and_import(resource_id)
