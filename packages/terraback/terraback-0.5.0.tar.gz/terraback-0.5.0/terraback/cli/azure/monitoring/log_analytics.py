from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.loganalytics import LogAnalyticsManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class LogAnalyticsWorkspacesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = LogAnalyticsManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_log_analytics_workspaces(self) -> List[Dict[str, Any]]:
        """List all Log Analytics workspaces in the subscription."""
        workspaces = []
        
        try:
            # List all Log Analytics workspaces
            for workspace in self.client.workspaces.list():
                try:
                    workspaces.append(self._process_log_analytics_workspace(workspace))
                except Exception as e:
                    logger.error(f"Error processing Log Analytics workspace {workspace.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Log Analytics workspaces: {str(e)}")
            
        return workspaces

    def _process_log_analytics_workspace(self, workspace) -> Dict[str, Any]:
        """Process a single Log Analytics workspace resource."""
        workspace_data = {
            "id": workspace.id,
            "name": workspace.name,
            "type": "azure_log_analytics_workspace",
            "resource_type": "azure_log_analytics_workspace",
            "resource_group_name": workspace.id.split('/')[4],
            "location": workspace.location,
            "properties": {
                "name": workspace.name,
                "location": workspace.location,
                "resource_group_name": workspace.id.split('/')[4],
            }
        }
        
        # Add SKU
        if workspace.sku and workspace.sku.name:
            workspace_data["properties"]["sku"] = workspace.sku.name
            
        # Add retention settings
        if hasattr(workspace, 'retention_in_days') and workspace.retention_in_days:
            workspace_data["properties"]["retention_in_days"] = workspace.retention_in_days
            
        # Add daily quota
        if hasattr(workspace, 'workspace_capping') and workspace.workspace_capping:
            if hasattr(workspace.workspace_capping, 'daily_quota_gb') and workspace.workspace_capping.daily_quota_gb:
                workspace_data["properties"]["daily_quota_gb"] = workspace.workspace_capping.daily_quota_gb
        
        # Add other properties
        if hasattr(workspace, 'force_cmk_for_query') and workspace.force_cmk_for_query is not None:
            workspace_data["properties"]["cmk_for_query_forced"] = workspace.force_cmk_for_query
            
        if hasattr(workspace, 'public_network_access_for_ingestion') and workspace.public_network_access_for_ingestion:
            workspace_data["properties"]["internet_ingestion_enabled"] = workspace.public_network_access_for_ingestion == "Enabled"
            
        if hasattr(workspace, 'public_network_access_for_query') and workspace.public_network_access_for_query:
            workspace_data["properties"]["internet_query_enabled"] = workspace.public_network_access_for_query == "Enabled"
            
        # Add reservation capacity
        if workspace.sku and hasattr(workspace.sku, 'capacity_reservation_level') and workspace.sku.capacity_reservation_level:
            workspace_data["properties"]["reservation_capacity_in_gb_per_day"] = workspace.sku.capacity_reservation_level
        
        # Add tags
        if workspace.tags:
            workspace_data["properties"]["tags"] = workspace.tags
            
        return workspace_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Log Analytics workspaces."""
        logger.info(f"Scanning Log Analytics workspaces in subscription {self.subscription_id}")
        return self.list_log_analytics_workspaces()


@require_professional
def scan_log_analytics_workspaces(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Log Analytics workspaces in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = LogAnalyticsWorkspacesScanner(credentials, subscription_id)
    log_analytics_workspaces = scanner.scan()
    
    if log_analytics_workspaces:
        # Generate Terraform files
        generate_tf_auto(log_analytics_workspaces, "azure_log_analytics_workspace", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(log_analytics_workspaces)} Azure Log Analytics Workspaces")
        
        # Generate import file
        generate_imports_file(
            "azure_log_analytics_workspace",
            log_analytics_workspaces,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return log_analytics_workspaces
