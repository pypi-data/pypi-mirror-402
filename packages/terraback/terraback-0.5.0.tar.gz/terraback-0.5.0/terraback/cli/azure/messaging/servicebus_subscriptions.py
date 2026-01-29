from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class ServiceBusSubscriptionsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ServiceBusManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_servicebus_subscriptions(self) -> List[Dict[str, Any]]:
        """List all Service Bus subscriptions in the subscription."""
        subscriptions = []
        
        try:
            # First get all namespaces
            for namespace in self.client.namespaces.list():
                resource_group_name = namespace.id.split('/')[4]
                
                # Get all topics for each namespace
                try:
                    for topic in self.client.topics.list_by_namespace(
                        resource_group_name=resource_group_name,
                        namespace_name=namespace.name
                    ):
                        # Get all subscriptions for each topic
                        try:
                            for subscription in self.client.subscriptions.list_by_topic(
                                resource_group_name=resource_group_name,
                                namespace_name=namespace.name,
                                topic_name=topic.name
                            ):
                                try:
                                    subscriptions.append(
                                        self._process_servicebus_subscription(
                                            subscription, 
                                            topic.id
                                        )
                                    )
                                except Exception as e:
                                    logger.error(
                                        f"Error processing Service Bus subscription {subscription.name}: {str(e)}"
                                    )
                                    continue
                        except HttpResponseError as e:
                            logger.error(
                                f"Error listing subscriptions for topic {topic.name}: {str(e)}"
                            )
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing topics for namespace {namespace.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Service Bus namespaces: {str(e)}")
            
        return subscriptions

    def _process_servicebus_subscription(self, subscription, topic_id: str) -> Dict[str, Any]:
        """Process a single Service Bus subscription resource."""
        subscription_data = {
            "id": subscription.id,
            "name": subscription.name,
            "type": "azure_servicebus_subscription",
            "resource_type": "azure_servicebus_subscription",
            "resource_group_name": subscription.id.split('/')[4],
            "properties": {
                "name": subscription.name,
                "topic_id": topic_id,
            }
        }
        
        # Add optional properties
        if hasattr(subscription, 'lock_duration') and subscription.lock_duration:
            subscription_data["properties"]["lock_duration"] = subscription.lock_duration
            
        if hasattr(subscription, 'requires_session') and subscription.requires_session is not None:
            subscription_data["properties"]["requires_session"] = subscription.requires_session
            
        if hasattr(subscription, 'default_message_time_to_live') and subscription.default_message_time_to_live:
            subscription_data["properties"]["default_message_ttl"] = subscription.default_message_time_to_live
            
        if hasattr(subscription, 'dead_lettering_on_message_expiration') and subscription.dead_lettering_on_message_expiration is not None:
            subscription_data["properties"]["dead_lettering_on_message_expiration"] = subscription.dead_lettering_on_message_expiration
            
        if hasattr(subscription, 'dead_lettering_on_filter_evaluation_error') and subscription.dead_lettering_on_filter_evaluation_error is not None:
            subscription_data["properties"]["dead_lettering_on_filter_evaluation_error"] = subscription.dead_lettering_on_filter_evaluation_error
            
        if hasattr(subscription, 'max_delivery_count') and subscription.max_delivery_count:
            subscription_data["properties"]["max_delivery_count"] = subscription.max_delivery_count
            
        if hasattr(subscription, 'status') and subscription.status:
            subscription_data["properties"]["status"] = subscription.status
            
        if hasattr(subscription, 'enable_batched_operations') and subscription.enable_batched_operations is not None:
            subscription_data["properties"]["enable_batched_operations"] = subscription.enable_batched_operations
            
        if hasattr(subscription, 'auto_delete_on_idle') and subscription.auto_delete_on_idle:
            subscription_data["properties"]["auto_delete_on_idle"] = subscription.auto_delete_on_idle
            
        if hasattr(subscription, 'forward_to') and subscription.forward_to:
            subscription_data["properties"]["forward_to"] = subscription.forward_to
            
        if hasattr(subscription, 'forward_dead_lettered_messages_to') and subscription.forward_dead_lettered_messages_to:
            subscription_data["properties"]["forward_dead_lettered_messages_to"] = subscription.forward_dead_lettered_messages_to
            
        return subscription_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Service Bus subscriptions."""
        logger.info(f"Scanning Service Bus subscriptions in subscription {self.subscription_id}")
        return self.list_servicebus_subscriptions()


@require_professional
def scan_servicebus_subscriptions(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Service Bus Subscriptions in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ServiceBusSubscriptionsScanner(credentials, subscription_id)
    servicebus_subscriptions = scanner.scan()
    
    if servicebus_subscriptions:
        # Generate Terraform files
        generate_tf_auto(servicebus_subscriptions, "azure_servicebus_subscription", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(servicebus_subscriptions)} Azure Service Bus Subscriptions")
        
        # Generate import file
        generate_imports_file(
            "azure_servicebus_subscription",
            servicebus_subscriptions,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return servicebus_subscriptions