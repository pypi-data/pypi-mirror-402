from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.cdn import CdnManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class CdnEndpointsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = CdnManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_cdn_endpoints(self) -> List[Dict[str, Any]]:
        """List all CDN endpoints in the subscription."""
        cdn_endpoints = []
        
        try:
            # First get all profiles
            for profile in self.client.profiles.list():
                resource_group_name = profile.id.split('/')[4]
                
                # Then get endpoints for each profile
                try:
                    for endpoint in self.client.endpoints.list_by_profile(
                        resource_group_name=resource_group_name,
                        profile_name=profile.name
                    ):
                        try:
                            cdn_endpoints.append(self._process_cdn_endpoint(endpoint, profile.name))
                        except Exception as e:
                            logger.error(f"Error processing CDN endpoint {endpoint.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing endpoints for profile {profile.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing CDN profiles: {str(e)}")
            
        return cdn_endpoints

    def _process_cdn_endpoint(self, endpoint, profile_name: str) -> Dict[str, Any]:
        """Process a single CDN endpoint resource."""
        cdn_endpoint_data = {
            "id": endpoint.id,
            "name": endpoint.name,
            "type": "azure_cdn_endpoint",
            "resource_type": "azure_cdn_endpoint",
            "resource_group_name": endpoint.id.split('/')[4],
            "location": endpoint.location,
            "properties": {
                "name": endpoint.name,
                "profile_name": profile_name,
                "location": endpoint.location,
                "resource_group_name": endpoint.id.split('/')[4],
                "origins": []
            }
        }
        
        # Process origins (required)
        if endpoint.origins:
            for origin in endpoint.origins:
                origin_data = {
                    "name": origin.name,
                    "host_name": origin.host_name
                }
                if origin.http_port:
                    origin_data["http_port"] = origin.http_port
                if origin.https_port:
                    origin_data["https_port"] = origin.https_port
                cdn_endpoint_data["properties"]["origins"].append(origin_data)
        
        # Add optional properties
        if endpoint.is_http_allowed is not None:
            cdn_endpoint_data["properties"]["is_http_allowed"] = endpoint.is_http_allowed
            
        if endpoint.is_https_allowed is not None:
            cdn_endpoint_data["properties"]["is_https_allowed"] = endpoint.is_https_allowed
            
        if endpoint.content_types_to_compress:
            cdn_endpoint_data["properties"]["content_types_to_compress"] = endpoint.content_types_to_compress
            
        if endpoint.is_compression_enabled is not None:
            cdn_endpoint_data["properties"]["is_compression_enabled"] = endpoint.is_compression_enabled
            
        if endpoint.query_string_caching_behavior:
            cdn_endpoint_data["properties"]["querystring_caching_behaviour"] = endpoint.query_string_caching_behavior
            
        if endpoint.optimization_type:
            cdn_endpoint_data["properties"]["optimization_type"] = endpoint.optimization_type
            
        if endpoint.origin_host_header:
            cdn_endpoint_data["properties"]["origin_host_header"] = endpoint.origin_host_header
            
        if endpoint.origin_path:
            cdn_endpoint_data["properties"]["origin_path"] = endpoint.origin_path
            
        if endpoint.probe_path:
            cdn_endpoint_data["properties"]["probe_path"] = endpoint.probe_path
        
        # Process geo filters
        if endpoint.geo_filters:
            geo_filters = []
            for filter in endpoint.geo_filters:
                geo_filters.append({
                    "relative_path": filter.relative_path,
                    "action": filter.action,
                    "country_codes": filter.country_codes
                })
            cdn_endpoint_data["properties"]["geo_filters"] = geo_filters
        
        # Process delivery rules
        if hasattr(endpoint, 'delivery_rules') and endpoint.delivery_rules:
            delivery_rules = []
            for rule in endpoint.delivery_rules:
                rule_data = {
                    "name": rule.name,
                    "order": rule.order
                }
                
                # Process conditions
                if rule.conditions:
                    for condition in rule.conditions:
                        if hasattr(condition, 'request_uri_condition'):
                            if "request_uri_conditions" not in rule_data:
                                rule_data["request_uri_conditions"] = []
                            rule_data["request_uri_conditions"].append({
                                "operator": condition.request_uri_condition.operator,
                                "match_values": condition.request_uri_condition.match_values,
                                "negate_condition": getattr(condition.request_uri_condition, 'negate_condition', False)
                            })
                
                # Process actions
                if rule.actions:
                    for action in rule.actions:
                        if hasattr(action, 'cache_expiration'):
                            rule_data["cache_expiration_action"] = {
                                "behavior": action.cache_expiration.behavior
                            }
                            if hasattr(action.cache_expiration, 'duration'):
                                rule_data["cache_expiration_action"]["duration"] = action.cache_expiration.duration
                                
                        if hasattr(action, 'response_header_action'):
                            if "modify_response_header_actions" not in rule_data:
                                rule_data["modify_response_header_actions"] = []
                            header_action = {
                                "action": action.response_header_action.action,
                                "name": action.response_header_action.header_name
                            }
                            if hasattr(action.response_header_action, 'value'):
                                header_action["value"] = action.response_header_action.value
                            rule_data["modify_response_header_actions"].append(header_action)
                
                delivery_rules.append(rule_data)
            
            if delivery_rules:
                cdn_endpoint_data["properties"]["delivery_rules"] = delivery_rules
        
        # Add tags
        if endpoint.tags:
            cdn_endpoint_data["properties"]["tags"] = endpoint.tags
            
        return cdn_endpoint_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all CDN endpoints."""
        logger.info(f"Scanning CDN endpoints in subscription {self.subscription_id}")
        return self.list_cdn_endpoints()


@require_professional
def scan_cdn_endpoints(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan CDN Endpoints in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = CdnEndpointsScanner(credentials, subscription_id)
    cdn_endpoints = scanner.scan()
    
    if cdn_endpoints:
        # Generate Terraform files
        generate_tf_auto(cdn_endpoints, "azure_cdn_endpoint", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(cdn_endpoints)} Azure CDN Endpoints")
        
        # Generate import file
        generate_imports_file(
            "azure_cdn_endpoint",
            cdn_endpoints,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return cdn_endpoints
