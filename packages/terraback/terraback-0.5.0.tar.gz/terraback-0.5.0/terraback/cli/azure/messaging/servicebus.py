from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.servicebus import ServiceBusManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class ServiceBusNamespacesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ServiceBusManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_servicebus_namespaces(self) -> List[Dict[str, Any]]:
        """List all Service Bus namespaces in the subscription."""
        namespaces = []
        
        try:
            # List all Service Bus namespaces
            for namespace in self.client.namespaces.list():
                try:
                    namespaces.append(self._process_servicebus_namespace(namespace))
                except Exception as e:
                    logger.error(f"Error processing Service Bus namespace {namespace.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Service Bus namespaces: {str(e)}")
            
        return namespaces

    def _process_servicebus_namespace(self, namespace) -> Dict[str, Any]:
        """Process a single Service Bus namespace resource."""
        namespace_data = {
            "id": namespace.id,
            "name": namespace.name,
            "type": "azure_servicebus_namespace",
            "resource_type": "azure_servicebus_namespace",
            "resource_group_name": namespace.id.split('/')[4],
            "location": namespace.location,
            "properties": {
                "name": namespace.name,
                "location": namespace.location,
                "resource_group_name": namespace.id.split('/')[4],
                "sku": namespace.sku.name,
            }
        }
        
        # Add optional properties
        if namespace.sku.capacity:
            namespace_data["properties"]["capacity"] = namespace.sku.capacity
            
        if hasattr(namespace, 'disable_local_auth') and namespace.disable_local_auth is not None:
            namespace_data["properties"]["local_auth_enabled"] = not namespace.disable_local_auth
            
        if hasattr(namespace, 'public_network_access') and namespace.public_network_access:
            namespace_data["properties"]["public_network_access_enabled"] = namespace.public_network_access == "Enabled"
            
        if hasattr(namespace, 'minimum_tls_version') and namespace.minimum_tls_version:
            namespace_data["properties"]["minimum_tls_version"] = namespace.minimum_tls_version
            
        if hasattr(namespace, 'zone_redundant') and namespace.zone_redundant is not None:
            namespace_data["properties"]["zone_redundant"] = namespace.zone_redundant
        
        # Identity
        if namespace.identity:
            identity_data = {
                "type": namespace.identity.type
            }
            if namespace.identity.user_assigned_identities:
                identity_data["identity_ids"] = list(namespace.identity.user_assigned_identities.keys())
            namespace_data["properties"]["identity"] = identity_data
        
        # Encryption
        if hasattr(namespace, 'encryption') and namespace.encryption:
            if namespace.encryption.key_vault_properties:
                for kvp in namespace.encryption.key_vault_properties:
                    if kvp.key_name and kvp.key_vault_uri:
                        namespace_data["properties"]["customer_managed_key"] = {
                            "key_vault_key_id": f"{kvp.key_vault_uri}keys/{kvp.key_name}/{kvp.key_version}" if kvp.key_version else f"{kvp.key_vault_uri}keys/{kvp.key_name}",
                            "identity_id": kvp.identity.user_assigned_identity if hasattr(kvp.identity, 'user_assigned_identity') else ""
                        }
                        break
        
        # Tags
        if namespace.tags:
            namespace_data["properties"]["tags"] = namespace.tags
            
        return namespace_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Service Bus namespaces."""
        logger.info(f"Scanning Service Bus namespaces in subscription {self.subscription_id}")
        return self.list_servicebus_namespaces()


@require_professional
def scan_servicebus_namespaces(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Service Bus Namespaces in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ServiceBusNamespacesScanner(credentials, subscription_id)
    servicebus_namespaces = scanner.scan()
    
    if servicebus_namespaces:
        # Generate Terraform files
        generate_tf_auto(servicebus_namespaces, "azure_servicebus_namespace", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(servicebus_namespaces)} Azure Service Bus Namespaces")
        
        # Generate import file
        generate_imports_file(
            "azure_servicebus_namespace",
            servicebus_namespaces,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return servicebus_namespaces
