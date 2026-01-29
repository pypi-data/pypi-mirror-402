from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.apimanagement import ApiManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result

logger = get_logger(__name__)


class ApiManagementApisScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ApiManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_api_management_apis(self) -> List[Dict[str, Any]]:
        """List all APIs in all API Management services."""
        apis = []
        
        try:
            # First get all API Management services
            for service in self.client.api_management_service.list():
                resource_group_name = service.id.split('/')[4]
                
                # Then get all APIs for each service
                try:
                    for api in self.client.api.list_by_service(
                        resource_group_name=resource_group_name,
                        service_name=service.name
                    ):
                        try:
                            apis.append(self._process_api(api, service.name, resource_group_name))
                        except Exception as e:
                            logger.error(f"Error processing API {api.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing APIs for service {service.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing API Management services: {str(e)}")
            
        return apis

    def _process_api(self, api, service_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Process a single API resource."""
        api_data = {
            "id": api.id,
            "name": f"{service_name}_{api.name}",
            "type": "azure_api_management_api",
            "resource_type": "azure_api_management_api",
            "resource_group_name": resource_group_name,
            "properties": {
                "name": api.name,
                "resource_group_name": resource_group_name,
                "api_management_name": service_name,
                "revision": api.api_revision or "1",
            }
        }
        
        # Add required properties
        if api.display_name:
            api_data["properties"]["display_name"] = api.display_name
            
        if api.path:
            api_data["properties"]["path"] = api.path
            
        if api.protocols:
            api_data["properties"]["protocols"] = list(api.protocols)
            
        if api.service_url:
            api_data["properties"]["service_url"] = api.service_url
        
        # Add optional properties
        if api.description:
            api_data["properties"]["description"] = api.description
            
        if hasattr(api, 'subscription_required') and api.subscription_required is not None:
            api_data["properties"]["subscription_required"] = api.subscription_required
            
        if api.type:
            # Map Azure API types to Terraform-compatible values
            type_mapping = {
                'Microsoft.ApiManagement/service/apis': 'http',  # Default to http
                'graphql': 'graphql',
                'soap': 'soap', 
                'websocket': 'websocket'
            }
            api_data["properties"]["api_type"] = type_mapping.get(api.type, 'http')
            
        if hasattr(api, 'api_revision_description') and api.api_revision_description:
            api_data["properties"]["revision_description"] = api.api_revision_description
            
        if api.api_version:
            api_data["properties"]["version"] = api.api_version
            
        if api.api_version_set_id:
            api_data["properties"]["version_set_id"] = api.api_version_set_id
        
        # Subscription key parameter names
        if hasattr(api, 'subscription_key_parameter_names') and api.subscription_key_parameter_names:
            api_data["properties"]["subscription_key_parameter_names"] = {
                "header": api.subscription_key_parameter_names.header,
                "query": api.subscription_key_parameter_names.query
            }
        
        # Source API ID for cloned APIs
        if hasattr(api, 'source_api_id') and api.source_api_id:
            api_data["properties"]["source_api_id"] = api.source_api_id
        
        # Authentication settings - handle with defensive coding
        if hasattr(api, 'authentication_settings') and api.authentication_settings:
            try:
                # OAuth2 authorization
                if hasattr(api.authentication_settings, 'oauth2') and api.authentication_settings.oauth2:
                    oauth2_auth = {}
                    if hasattr(api.authentication_settings.oauth2, 'authorization_server_id') and api.authentication_settings.oauth2.authorization_server_id:
                        oauth2_auth["authorization_server_name"] = api.authentication_settings.oauth2.authorization_server_id.split('/')[-1]
                    if hasattr(api.authentication_settings.oauth2, 'scope') and api.authentication_settings.oauth2.scope:
                        oauth2_auth["scope"] = api.authentication_settings.oauth2.scope
                    if oauth2_auth:
                        api_data["properties"]["oauth2_authorization"] = oauth2_auth
                
                # OpenID authentication
                if hasattr(api.authentication_settings, 'openid') and api.authentication_settings.openid:
                    openid_auth = {}
                    if hasattr(api.authentication_settings.openid, 'openid_provider_id') and api.authentication_settings.openid.openid_provider_id:
                        openid_auth["openid_provider_name"] = api.authentication_settings.openid.openid_provider_id.split('/')[-1]
                    if hasattr(api.authentication_settings.openid, 'bearer_token_sending_methods') and api.authentication_settings.openid.bearer_token_sending_methods:
                        openid_auth["bearer_token_sending_methods"] = list(api.authentication_settings.openid.bearer_token_sending_methods)
                    if openid_auth:
                        api_data["properties"]["openid_authentication"] = openid_auth
            except Exception as e:
                logger.warning(f"Could not process authentication settings for API {api.name}: {str(e)}")
        
        return api_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all APIs."""
        logger.info(f"Scanning API Management APIs in subscription {self.subscription_id}")
        return self.list_api_management_apis()


def scan_api_management_apis(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan API Management APIs in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ApiManagementApisScanner(credentials, subscription_id)
    api_management_apis = scanner.scan()
    
    if api_management_apis:
        # Generate Terraform files
        generate_tf_auto(api_management_apis, "azure_api_management_api", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(api_management_apis)} Azure API Management APIs")
        
        # Generate import file
        generate_imports_file(
            "azure_api_management_api",
            api_management_apis,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return api_management_apis
