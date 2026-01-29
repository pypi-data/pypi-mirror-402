from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.apimanagement import ApiManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class ApiManagementScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ApiManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_api_management_services(self) -> List[Dict[str, Any]]:
        """List all API Management services in the subscription."""
        api_management_services = []
        
        try:
            # List all API Management services
            for service in self.client.api_management_service.list():
                try:
                    api_management_services.append(self._process_api_management_service(service))
                except Exception as e:
                    logger.error(f"Error processing API Management service {service.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing API Management services: {str(e)}")
            
        return api_management_services

    def _process_api_management_service(self, service) -> Dict[str, Any]:
        """Process a single API Management service resource."""
        service_data = {
            "id": service.id,
            "name": service.name,
            "type": "azure_api_management",
            "resource_type": "azure_api_management",
            "resource_group_name": service.id.split('/')[4],
            "location": service.location,
            "properties": {
                "name": service.name,
                "location": service.location,
                "resource_group_name": service.id.split('/')[4],
                "publisher_name": service.publisher_name,
                "publisher_email": service.publisher_email,
                "sku_name": f"{service.sku.name}_{service.sku.capacity}",
            }
        }
        
        # Add optional properties
        if hasattr(service, 'virtual_network_type') and service.virtual_network_type:
            service_data["properties"]["virtual_network_type"] = service.virtual_network_type
            
        # Note: management_api_url, portal_url, gateway_url, gateway_regional_url are computed attributes
        # They are set by Azure automatically and should not be included in Terraform configuration
            
        if hasattr(service, 'public_ip_address_id') and service.public_ip_address_id:
            service_data["properties"]["public_ip_address_id"] = service.public_ip_address_id
            
        if hasattr(service, 'notification_sender_email') and service.notification_sender_email:
            service_data["properties"]["notification_sender_email"] = service.notification_sender_email
        
        # Process policies
        if hasattr(service, 'policies') and service.policies:
            service_data["properties"]["policy"] = {
                "xml_content": service.policies
            }
        
        # Process protocols
        if hasattr(service, 'enable_client_certificate') and service.enable_client_certificate is not None:
            service_data["properties"]["protocols"] = {
                "enable_http2": getattr(service, 'enable_http2', False)
            }
        
        # Process security settings - use new property names for compatibility
        security = {}
        if hasattr(service, 'custom_properties') and service.custom_properties:
            props = service.custom_properties
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30' in props:
                security['enable_backend_ssl30'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10' in props:
                security['enable_backend_tls10'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11' in props:
                security['enable_backend_tls11'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30' in props:
                security['enable_frontend_ssl30'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10' in props:
                security['enable_frontend_tls10'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11' in props:
                security['enable_frontend_tls11'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11'] == 'True'
            if 'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168' in props:
                security['triple_des_ciphers_enabled'] = props['Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Ciphers.TripleDes168'] == 'True'
        
        if security:
            service_data["properties"]["security"] = security
        
        # Process identity
        if service.identity:
            identity_data = {
                "type": service.identity.type
            }
            if service.identity.user_assigned_identities:
                identity_data["identity_ids"] = list(service.identity.user_assigned_identities.keys())
            service_data["properties"]["identity"] = identity_data
        
        # Process virtual network configuration
        if service.virtual_network_configuration:
            service_data["properties"]["virtual_network_configuration"] = {
                "subnet_id": service.virtual_network_configuration.subnet_resource_id
            }
        
        # Process additional locations
        if hasattr(service, 'additional_locations') and service.additional_locations:
            additional_locations = []
            for location in service.additional_locations:
                location_data = {
                    "location": location.location
                }
                if location.sku and location.sku.capacity:
                    location_data["capacity"] = location.sku.capacity
                if hasattr(location, 'zones') and location.zones:
                    location_data["zones"] = location.zones
                if hasattr(location, 'public_ip_address_id') and location.public_ip_address_id:
                    location_data["public_ip_address_id"] = location.public_ip_address_id
                if location.virtual_network_configuration:
                    location_data["virtual_network_configuration"] = {
                        "subnet_id": location.virtual_network_configuration.subnet_resource_id
                    }
                if hasattr(location, 'disable_gateway') and location.disable_gateway:
                    location_data["gateway_disabled"] = location.disable_gateway
                additional_locations.append(location_data)
            service_data["properties"]["additional_location"] = additional_locations
        
        # Process hostname configurations
        if hasattr(service, 'hostname_configurations') and service.hostname_configurations:
            hostname_config = {
                "management": [],
                "portal": [],
                "developer_portal": [],
                "proxy": [],
                "scm": []
            }
            
            for config in service.hostname_configurations:
                config_data = {
                    "host_name": config.host_name,
                    "key_vault_id": config.key_vault_id if hasattr(config, 'key_vault_id') else "",
                }
                if hasattr(config, 'certificate') and config.certificate:
                    config_data["certificate"] = config.certificate
                if hasattr(config, 'certificate_password') and config.certificate_password:
                    config_data["certificate_password"] = config.certificate_password
                if hasattr(config, 'negotiate_client_certificate') and config.negotiate_client_certificate is not None:
                    config_data["negotiate_client_certificate"] = config.negotiate_client_certificate
                
                if config.type == "Proxy":
                    if hasattr(config, 'default_ssl_binding') and config.default_ssl_binding is not None:
                        config_data["default_ssl_binding"] = config.default_ssl_binding
                    hostname_config["proxy"].append(config_data)
                elif config.type == "Portal":
                    hostname_config["portal"].append(config_data)
                elif config.type == "Management":
                    hostname_config["management"].append(config_data)
                elif config.type == "DeveloperPortal":
                    hostname_config["developer_portal"].append(config_data)
                elif config.type == "Scm":
                    hostname_config["scm"].append(config_data)
            
            # Only add non-empty configurations
            filtered_hostname_config = {k: v for k, v in hostname_config.items() if v}
            if filtered_hostname_config:
                service_data["properties"]["hostname_configuration"] = filtered_hostname_config
        
        # Add zones if available
        if hasattr(service, 'zones') and service.zones:
            service_data["properties"]["zones"] = service.zones
        
        # Note: sign_in and sign_up settings are typically configured separately 
        # via the API Management portal settings, not available in the service object
        # These would need to be retrieved via separate API calls if needed
        
        # Add tags
        if service.tags:
            service_data["properties"]["tags"] = service.tags
            
        return service_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all API Management services."""
        logger.info(f"Scanning API Management services in subscription {self.subscription_id}")
        return self.list_api_management_services()


@require_professional
def scan_api_management(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan API Management Services in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ApiManagementScanner(credentials, subscription_id)
    api_management = scanner.scan()
    
    if api_management:
        # Generate Terraform files
        generate_tf_auto(api_management, "azure_api_management", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(api_management)} Azure API Management Services")
        
        # Generate import file
        generate_imports_file(
            "azure_api_management",
            api_management,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return api_management
