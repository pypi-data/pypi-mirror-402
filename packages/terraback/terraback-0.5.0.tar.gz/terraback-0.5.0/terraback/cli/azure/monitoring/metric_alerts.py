from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.monitor import MonitorManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class MetricAlertsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = MonitorManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_metric_alerts(self) -> List[Dict[str, Any]]:
        """List all metric alerts in the subscription."""
        metric_alerts = []
        
        try:
            # List all metric alerts
            for alert in self.client.metric_alerts.list_by_subscription():
                try:
                    metric_alerts.append(self._process_metric_alert(alert))
                except Exception as e:
                    logger.error(f"Error processing metric alert {alert.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing metric alerts: {str(e)}")
            
        return metric_alerts

    def _process_metric_alert(self, alert) -> Dict[str, Any]:
        """Process a single metric alert resource."""
        alert_data = {
            "id": alert.id,
            "name": alert.name,
            "type": "azure_metric_alert",
            "resource_type": "azure_metric_alert",
            "resource_group_name": alert.id.split('/')[4],
            "location": alert.location,
            "properties": {
                "name": alert.name,
                "resource_group_name": alert.id.split('/')[4],
                "scopes": alert.scopes,
            }
        }
        
        # Add basic properties
        if alert.description:
            alert_data["properties"]["description"] = alert.description
            
        if hasattr(alert, 'enabled') and alert.enabled is not None:
            alert_data["properties"]["enabled"] = alert.enabled
            
        if hasattr(alert, 'auto_mitigate') and alert.auto_mitigate is not None:
            alert_data["properties"]["auto_mitigate"] = alert.auto_mitigate
            
        if alert.evaluation_frequency:
            alert_data["properties"]["frequency"] = alert.evaluation_frequency
            
        if alert.severity is not None:
            alert_data["properties"]["severity"] = alert.severity
            
        if hasattr(alert, 'target_resource_type') and alert.target_resource_type:
            alert_data["properties"]["target_resource_type"] = alert.target_resource_type
            
        if hasattr(alert, 'target_resource_region') and alert.target_resource_region:
            alert_data["properties"]["target_resource_location"] = alert.target_resource_region
            
        if alert.window_size:
            alert_data["properties"]["window_size"] = alert.window_size
        
        # Process criteria
        if alert.criteria:
            if hasattr(alert.criteria, 'all_of') and alert.criteria.all_of:
                # Static criteria
                criteria_list = []
                for criterion in alert.criteria.all_of:
                    criteria_item = {
                        "metric_namespace": criterion.metric_namespace,
                        "metric_name": criterion.metric_name,
                        "aggregation": criterion.time_aggregation,
                        "operator": criterion.operator,
                        "threshold": criterion.threshold
                    }
                    
                    if hasattr(criterion, 'skip_metric_validation') and criterion.skip_metric_validation is not None:
                        criteria_item["skip_metric_validation"] = criterion.skip_metric_validation
                    
                    if hasattr(criterion, 'dimensions') and criterion.dimensions:
                        criteria_item["dimensions"] = [
                            {
                                "name": d.name,
                                "operator": d.operator,
                                "values": d.values
                            } for d in criterion.dimensions
                        ]
                    
                    criteria_list.append(criteria_item)
                
                alert_data["properties"]["criteria"] = criteria_list
                
            elif hasattr(alert.criteria, 'odata.type') and 'DynamicThresholdCriterion' in alert.criteria.odata_type:
                # Dynamic criteria
                dynamic_criteria = []
                for criterion in alert.criteria.all_of:
                    criteria_item = {
                        "metric_namespace": criterion.metric_namespace,
                        "metric_name": criterion.metric_name,
                        "aggregation": criterion.time_aggregation,
                        "operator": criterion.operator,
                        "alert_sensitivity": criterion.alert_sensitivity
                    }
                    
                    if hasattr(criterion, 'failing_periods'):
                        if hasattr(criterion.failing_periods, 'min_failing_periods_to_alert'):
                            criteria_item["evaluation_failure_count"] = criterion.failing_periods.min_failing_periods_to_alert
                        if hasattr(criterion.failing_periods, 'number_of_evaluation_periods'):
                            criteria_item["evaluation_total_count"] = criterion.failing_periods.number_of_evaluation_periods
                    
                    if hasattr(criterion, 'ignore_data_before') and criterion.ignore_data_before:
                        criteria_item["ignore_data_before"] = criterion.ignore_data_before
                    
                    if hasattr(criterion, 'skip_metric_validation') and criterion.skip_metric_validation is not None:
                        criteria_item["skip_metric_validation"] = criterion.skip_metric_validation
                    
                    if hasattr(criterion, 'dimensions') and criterion.dimensions:
                        criteria_item["dimensions"] = [
                            {
                                "name": d.name,
                                "operator": d.operator,
                                "values": d.values
                            } for d in criterion.dimensions
                        ]
                    
                    dynamic_criteria.append(criteria_item)
                
                alert_data["properties"]["dynamic_criteria"] = dynamic_criteria
                
            elif hasattr(alert.criteria, 'odata.type') and 'WebtestLocationAvailabilityCriteria' in alert.criteria.odata_type:
                # Web test criteria
                alert_data["properties"]["application_insights_web_test_location_availability_criteria"] = {
                    "web_test_id": alert.criteria.web_test_id,
                    "component_id": alert.criteria.component_id,
                    "failed_location_count": alert.criteria.failed_location_count
                }
        
        # Process actions
        if alert.actions and len(alert.actions) > 0:
            actions = []
            for action in alert.actions:
                action_item = {
                    "action_group_id": action.action_group_id
                }
                if hasattr(action, 'webhook_properties') and action.webhook_properties:
                    action_item["webhook_properties"] = action.webhook_properties
                actions.append(action_item)
            alert_data["properties"]["action"] = actions
        
        # Add tags
        if alert.tags:
            alert_data["properties"]["tags"] = alert.tags
            
        return alert_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all metric alerts."""
        logger.info(f"Scanning metric alerts in subscription {self.subscription_id}")
        return self.list_metric_alerts()


@require_professional
def scan_metric_alerts(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure Metric Alerts in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = MetricAlertsScanner(credentials, subscription_id)
    metric_alerts = scanner.scan()
    
    if metric_alerts:
        # Generate Terraform files
        generate_tf_auto(metric_alerts, "azure_metric_alert", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(metric_alerts)} Azure Metric Alerts")
        
        # Generate import file
        generate_imports_file(
            "azure_metric_alert",
            metric_alerts,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return metric_alerts
