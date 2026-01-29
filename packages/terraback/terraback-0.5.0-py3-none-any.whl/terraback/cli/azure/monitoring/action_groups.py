from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.monitor import MonitorManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional
from terraback.cli.azure.common.utils import normalize_resource_id

logger = get_logger(__name__)


class ActionGroupsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = MonitorManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_action_groups(self) -> List[Dict[str, Any]]:
        """List all action groups in the subscription."""
        action_groups = []
        
        try:
            # List all action groups
            for action_group in self.client.action_groups.list_by_subscription_id():
                try:
                    action_groups.append(self._process_action_group(action_group))
                except Exception as e:
                    logger.error(f"Error processing action group {action_group.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing action groups: {str(e)}")
            
        return action_groups

    def _process_action_group(self, action_group) -> Dict[str, Any]:
        """Process a single action group resource."""
        # Normalize the resource ID
        normalized_id = normalize_resource_id(action_group.id)
        
        action_group_data = {
            "id": normalized_id,
            "name": action_group.name,
            "type": "azure_monitor_action_group",
            "resource_type": "azure_monitor_action_group",
            "resource_group_name": normalized_id.split('/')[4],
            "location": action_group.location if hasattr(action_group, 'location') else "global",
            "properties": {
                "name": action_group.name,
                "resource_group_name": normalized_id.split('/')[4],
                "short_name": action_group.group_short_name,
            }
        }
        
        # Add enabled status
        if hasattr(action_group, 'enabled') and action_group.enabled is not None:
            action_group_data["properties"]["enabled"] = action_group.enabled
        
        # Process receivers
        if hasattr(action_group, 'arm_role_receivers') and action_group.arm_role_receivers:
            action_group_data["properties"]["arm_role_receivers"] = [
                {
                    "name": r.name,
                    "role_id": r.role_id,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.arm_role_receivers
            ]
        
        if hasattr(action_group, 'automation_runbook_receivers') and action_group.automation_runbook_receivers:
            action_group_data["properties"]["automation_runbook_receivers"] = [
                {
                    "name": r.name,
                    "automation_account_id": r.automation_account_id,
                    "runbook_name": r.runbook_name,
                    "webhook_resource_id": r.webhook_resource_id,
                    "is_global_runbook": r.is_global_runbook,
                    "service_uri": r.service_uri,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.automation_runbook_receivers
            ]
        
        if hasattr(action_group, 'azure_app_push_receivers') and action_group.azure_app_push_receivers:
            action_group_data["properties"]["azure_app_push_receivers"] = [
                {
                    "name": r.name,
                    "email_address": r.email_address
                } for r in action_group.azure_app_push_receivers
            ]
        
        if hasattr(action_group, 'azure_function_receivers') and action_group.azure_function_receivers:
            action_group_data["properties"]["azure_function_receivers"] = [
                {
                    "name": r.name,
                    "function_app_resource_id": r.function_app_resource_id,
                    "function_name": r.function_name,
                    "http_trigger_url": r.http_trigger_url,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.azure_function_receivers
            ]
        
        if hasattr(action_group, 'email_receivers') and action_group.email_receivers:
            action_group_data["properties"]["email_receivers"] = [
                {
                    "name": r.name,
                    "email_address": r.email_address,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.email_receivers
            ]
        
        if hasattr(action_group, 'event_hub_receivers') and action_group.event_hub_receivers:
            action_group_data["properties"]["event_hub_receivers"] = [
                {
                    "name": r.name,
                    "event_hub_namespace": r.event_hub_name_space,
                    "event_hub_name": r.event_hub_name,
                    "subscription_id": r.subscription_id or self.subscription_id,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.event_hub_receivers
            ]
        
        if hasattr(action_group, 'itsm_receivers') and action_group.itsm_receivers:
            action_group_data["properties"]["itsm_receivers"] = [
                {
                    "name": r.name,
                    "workspace_id": r.workspace_id,
                    "connection_id": r.connection_id,
                    "ticket_configuration": r.ticket_configuration,
                    "region": r.region
                } for r in action_group.itsm_receivers
            ]
        
        if hasattr(action_group, 'logic_app_receivers') and action_group.logic_app_receivers:
            action_group_data["properties"]["logic_app_receivers"] = [
                {
                    "name": r.name,
                    "resource_id": r.resource_id,
                    "callback_url": r.callback_url,
                    "use_common_alert_schema": r.use_common_alert_schema
                } for r in action_group.logic_app_receivers
            ]
        
        if hasattr(action_group, 'sms_receivers') and action_group.sms_receivers:
            action_group_data["properties"]["sms_receivers"] = [
                {
                    "name": r.name,
                    "country_code": r.country_code,
                    "phone_number": r.phone_number
                } for r in action_group.sms_receivers
            ]
        
        if hasattr(action_group, 'voice_receivers') and action_group.voice_receivers:
            action_group_data["properties"]["voice_receivers"] = [
                {
                    "name": r.name,
                    "country_code": r.country_code,
                    "phone_number": r.phone_number
                } for r in action_group.voice_receivers
            ]
        
        if hasattr(action_group, 'webhook_receivers') and action_group.webhook_receivers:
            webhook_receivers = []
            for r in action_group.webhook_receivers:
                receiver = {
                    "name": r.name,
                    "service_uri": r.service_uri,
                    "use_common_alert_schema": r.use_common_alert_schema
                }
                if hasattr(r, 'aad_auth') and r.aad_auth:
                    receiver["aad_auth"] = {
                        "object_id": r.aad_auth.object_id,
                        "identifier_uri": r.aad_auth.identifier_uri,
                        "tenant_id": r.aad_auth.tenant_id
                    }
                webhook_receivers.append(receiver)
            action_group_data["properties"]["webhook_receivers"] = webhook_receivers
        
        # Add tags
        if action_group.tags:
            action_group_data["properties"]["tags"] = action_group.tags
            
        return action_group_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all action groups."""
        logger.info(f"Scanning action groups in subscription {self.subscription_id}")
        return self.list_action_groups()


@require_professional
def scan_action_groups(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure Action Groups in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ActionGroupsScanner(credentials, subscription_id)
    action_groups = scanner.scan()
    
    if action_groups:    # Process resources before generation
        action_groups = process_resources(action_groups, "azure_monitor_action_group")
    

        # Generate Terraform files
        generate_tf_auto(action_groups, "azure_monitor_action_group", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(action_groups)} Azure Action Groups")
        
        # Generate import file
        generate_imports_file(
            "azure_monitor_action_group",
            action_groups,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return action_groups
