from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import timedelta
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional
from terraback.cli.azure.common.utils import timedelta_to_iso8601

logger = get_logger(__name__)


class ServiceBusQueuesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ServiceBusManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_servicebus_queues(self) -> List[Dict[str, Any]]:
        """List all Service Bus queues in the subscription."""
        queues = []
        
        try:
            # First get all namespaces
            for namespace in self.client.namespaces.list():
                resource_group_name = namespace.id.split('/')[4]
                
                # Then get all queues for each namespace
                try:
                    for queue in self.client.queues.list_by_namespace(
                        resource_group_name=resource_group_name,
                        namespace_name=namespace.name
                    ):
                        try:
                            queues.append(self._process_servicebus_queue(queue, namespace.id))
                        except Exception as e:
                            logger.error(f"Error processing Service Bus queue {queue.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing queues for namespace {namespace.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Service Bus namespaces: {str(e)}")
            
        return queues

    def _process_servicebus_queue(self, queue, namespace_id: str) -> Dict[str, Any]:
        """Process a single Service Bus queue resource."""
        queue_data = {
            "id": queue.id,
            "name": queue.name,
            "type": "azure_servicebus_queue",
            "resource_type": "azure_servicebus_queue",
            "resource_group_name": queue.id.split('/')[4],
            "properties": {
                "name": queue.name,
                "namespace_id": namespace_id,
            }
        }
        
        # Add optional properties
        if hasattr(queue, 'lock_duration') and queue.lock_duration:
            if isinstance(queue.lock_duration, timedelta):
                queue_data["properties"]["lock_duration"] = timedelta_to_iso8601(queue.lock_duration)
            else:
                queue_data["properties"]["lock_duration"] = queue.lock_duration
            
        if hasattr(queue, 'max_message_size_in_kilobytes') and queue.max_message_size_in_kilobytes:
            queue_data["properties"]["max_message_size_in_kilobytes"] = queue.max_message_size_in_kilobytes
            
        if hasattr(queue, 'max_size_in_megabytes') and queue.max_size_in_megabytes:
            queue_data["properties"]["max_size_in_megabytes"] = queue.max_size_in_megabytes
            
        if hasattr(queue, 'requires_duplicate_detection') and queue.requires_duplicate_detection is not None:
            queue_data["properties"]["requires_duplicate_detection"] = queue.requires_duplicate_detection
            
        if hasattr(queue, 'requires_session') and queue.requires_session is not None:
            queue_data["properties"]["requires_session"] = queue.requires_session
            
        if hasattr(queue, 'default_message_time_to_live') and queue.default_message_time_to_live:
            if isinstance(queue.default_message_time_to_live, timedelta):
                queue_data["properties"]["default_message_ttl"] = timedelta_to_iso8601(queue.default_message_time_to_live)
            else:
                queue_data["properties"]["default_message_ttl"] = queue.default_message_time_to_live
            
        if hasattr(queue, 'dead_lettering_on_message_expiration') and queue.dead_lettering_on_message_expiration is not None:
            queue_data["properties"]["dead_lettering_on_message_expiration"] = queue.dead_lettering_on_message_expiration
            
        if hasattr(queue, 'duplicate_detection_history_time_window') and queue.duplicate_detection_history_time_window:
            if isinstance(queue.duplicate_detection_history_time_window, timedelta):
                queue_data["properties"]["duplicate_detection_history_time_window"] = timedelta_to_iso8601(queue.duplicate_detection_history_time_window)
            else:
                queue_data["properties"]["duplicate_detection_history_time_window"] = queue.duplicate_detection_history_time_window
            
        if hasattr(queue, 'max_delivery_count') and queue.max_delivery_count:
            queue_data["properties"]["max_delivery_count"] = queue.max_delivery_count
            
        if hasattr(queue, 'status') and queue.status:
            queue_data["properties"]["status"] = queue.status
            
        if hasattr(queue, 'enable_batched_operations') and queue.enable_batched_operations is not None:
            queue_data["properties"]["enable_batched_operations"] = queue.enable_batched_operations
            
        if hasattr(queue, 'auto_delete_on_idle') and queue.auto_delete_on_idle:
            if isinstance(queue.auto_delete_on_idle, timedelta):
                queue_data["properties"]["auto_delete_on_idle"] = timedelta_to_iso8601(queue.auto_delete_on_idle)
            else:
                queue_data["properties"]["auto_delete_on_idle"] = queue.auto_delete_on_idle
            
        if hasattr(queue, 'enable_partitioning') and queue.enable_partitioning is not None:
            queue_data["properties"]["enable_partitioning"] = queue.enable_partitioning
            
        if hasattr(queue, 'enable_express') and queue.enable_express is not None:
            queue_data["properties"]["enable_express"] = queue.enable_express
            
        if hasattr(queue, 'forward_to') and queue.forward_to:
            queue_data["properties"]["forward_to"] = queue.forward_to
            
        if hasattr(queue, 'forward_dead_lettered_messages_to') and queue.forward_dead_lettered_messages_to:
            queue_data["properties"]["forward_dead_lettered_messages_to"] = queue.forward_dead_lettered_messages_to
            
        return queue_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Service Bus queues."""
        logger.info(f"Scanning Service Bus queues in subscription {self.subscription_id}")
        return self.list_servicebus_queues()


@require_professional
def scan_servicebus_queues(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Service Bus Queues in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ServiceBusQueuesScanner(credentials, subscription_id)
    servicebus_queues = scanner.scan()
    
    if servicebus_queues:
        # Generate Terraform files
        generate_tf_auto(servicebus_queues, "azure_servicebus_queue", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(servicebus_queues)} Azure Service Bus Queues")
        
        # Generate import file
        generate_imports_file(
            "azure_servicebus_queue",
            servicebus_queues,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return servicebus_queues
