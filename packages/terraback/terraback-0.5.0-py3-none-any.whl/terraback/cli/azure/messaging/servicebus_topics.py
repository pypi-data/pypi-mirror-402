from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class ServiceBusTopicsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ServiceBusManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_servicebus_topics(self) -> List[Dict[str, Any]]:
        """List all Service Bus topics in the subscription."""
        topics = []
        
        try:
            # First get all namespaces
            for namespace in self.client.namespaces.list():
                resource_group_name = namespace.id.split('/')[4]
                
                # Then get all topics for each namespace
                try:
                    for topic in self.client.topics.list_by_namespace(
                        resource_group_name=resource_group_name,
                        namespace_name=namespace.name
                    ):
                        try:
                            topics.append(self._process_servicebus_topic(topic, namespace.id))
                        except Exception as e:
                            logger.error(f"Error processing Service Bus topic {topic.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing topics for namespace {namespace.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Service Bus namespaces: {str(e)}")
            
        return topics

    def _process_servicebus_topic(self, topic, namespace_id: str) -> Dict[str, Any]:
        """Process a single Service Bus topic resource."""
        topic_data = {
            "id": topic.id,
            "name": topic.name,
            "type": "azure_servicebus_topic",
            "resource_type": "azure_servicebus_topic",
            "resource_group_name": topic.id.split('/')[4],
            "properties": {
                "name": topic.name,
                "namespace_id": namespace_id,
            }
        }
        
        # Add optional properties
        if hasattr(topic, 'max_message_size_in_kilobytes') and topic.max_message_size_in_kilobytes:
            topic_data["properties"]["max_message_size_in_kilobytes"] = topic.max_message_size_in_kilobytes
            
        if hasattr(topic, 'max_size_in_megabytes') and topic.max_size_in_megabytes:
            topic_data["properties"]["max_size_in_megabytes"] = topic.max_size_in_megabytes
            
        if hasattr(topic, 'requires_duplicate_detection') and topic.requires_duplicate_detection is not None:
            topic_data["properties"]["requires_duplicate_detection"] = topic.requires_duplicate_detection
            
        if hasattr(topic, 'default_message_time_to_live') and topic.default_message_time_to_live:
            topic_data["properties"]["default_message_ttl"] = topic.default_message_time_to_live
            
        if hasattr(topic, 'duplicate_detection_history_time_window') and topic.duplicate_detection_history_time_window:
            topic_data["properties"]["duplicate_detection_history_time_window"] = topic.duplicate_detection_history_time_window
            
        if hasattr(topic, 'status') and topic.status:
            topic_data["properties"]["status"] = topic.status
            
        if hasattr(topic, 'enable_batched_operations') and topic.enable_batched_operations is not None:
            topic_data["properties"]["enable_batched_operations"] = topic.enable_batched_operations
            
        if hasattr(topic, 'auto_delete_on_idle') and topic.auto_delete_on_idle:
            topic_data["properties"]["auto_delete_on_idle"] = topic.auto_delete_on_idle
            
        if hasattr(topic, 'enable_partitioning') and topic.enable_partitioning is not None:
            topic_data["properties"]["enable_partitioning"] = topic.enable_partitioning
            
        if hasattr(topic, 'enable_express') and topic.enable_express is not None:
            topic_data["properties"]["enable_express"] = topic.enable_express
            
        if hasattr(topic, 'support_ordering') and topic.support_ordering is not None:
            topic_data["properties"]["support_ordering"] = topic.support_ordering
            
        return topic_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Service Bus topics."""
        logger.info(f"Scanning Service Bus topics in subscription {self.subscription_id}")
        return self.list_servicebus_topics()


@require_professional
def scan_servicebus_topics(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Service Bus Topics in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ServiceBusTopicsScanner(credentials, subscription_id)
    servicebus_topics = scanner.scan()
    
    if servicebus_topics:
        # Generate Terraform files
        generate_tf_auto(servicebus_topics, "azure_servicebus_topic", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(servicebus_topics)} Azure Service Bus Topics")
        
        # Generate import file
        generate_imports_file(
            "azure_servicebus_topic",
            servicebus_topics,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return servicebus_topics