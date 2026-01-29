from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.cli.azure.resource_processor import process_resources

logger = get_logger(__name__)


class PublicIPsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = NetworkManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_public_ips(self) -> List[Dict[str, Any]]:
        """List all public IPs in the subscription."""
        public_ips = []
        
        try:
            # List all public IPs
            for public_ip in self.client.public_ip_addresses.list_all():
                try:
                    public_ips.append(self._process_public_ip(public_ip))
                except Exception as e:
                    logger.error(f"Error processing public IP {public_ip.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing public IPs: {str(e)}")
            
        return public_ips

    def _process_public_ip(self, public_ip) -> Dict[str, Any]:
        """Process a single public IP resource."""
        public_ip_data = {
            "id": public_ip.id,
            "name": public_ip.name,
            "type": "azure_public_ip",
            "resource_type": "azure_public_ip",
            "resource_group_name": public_ip.id.split('/')[4],
            "location": public_ip.location,
            "properties": {
                "name": public_ip.name,
                "location": public_ip.location,
                "resource_group_name": public_ip.id.split('/')[4],
                "allocation_method": public_ip.public_ip_allocation_method,
            }
        }
        
        # Add SKU
        if public_ip.sku:
            public_ip_data["properties"]["sku"] = public_ip.sku.name
            if public_ip.sku.tier:
                public_ip_data["properties"]["sku_tier"] = public_ip.sku.tier
        
        # Add zones
        if public_ip.zones:
            public_ip_data["properties"]["zones"] = public_ip.zones
        
        # Add DNS settings
        if public_ip.dns_settings:
            if public_ip.dns_settings.domain_name_label:
                public_ip_data["properties"]["domain_name_label"] = public_ip.dns_settings.domain_name_label
            if public_ip.dns_settings.reverse_fqdn:
                public_ip_data["properties"]["reverse_fqdn"] = public_ip.dns_settings.reverse_fqdn
        
        # Add other properties
        if hasattr(public_ip, 'edge_zone') and public_ip.edge_zone:
            public_ip_data["properties"]["edge_zone"] = public_ip.edge_zone
            
        if public_ip.idle_timeout_in_minutes:
            public_ip_data["properties"]["idle_timeout_in_minutes"] = public_ip.idle_timeout_in_minutes
            
        if public_ip.public_ip_address_version:
            public_ip_data["properties"]["ip_version"] = public_ip.public_ip_address_version
            
        if hasattr(public_ip, 'public_ip_prefix') and public_ip.public_ip_prefix:
            public_ip_data["properties"]["public_ip_prefix_id"] = public_ip.public_ip_prefix.id
        
        # Add metadata
        if hasattr(public_ip, 'ip_address') and public_ip.ip_address:
            public_ip_data["properties"]["ip_address"] = public_ip.ip_address
            
        if hasattr(public_ip, 'fqdn') and public_ip.dns_settings and public_ip.dns_settings.fqdn:
            public_ip_data["properties"]["fqdn"] = public_ip.dns_settings.fqdn
        
        # Add associated resource info if available
        if hasattr(public_ip, 'ip_configuration') and public_ip.ip_configuration:
            public_ip_data["properties"]["associated_resource_id"] = public_ip.ip_configuration.id
            public_ip_data["properties"]["associated_resource_type"] = public_ip.ip_configuration.id.split('/')[-3]
        
        # Add tags
        if public_ip.tags:
            public_ip_data["properties"]["tags"] = public_ip.tags
            
        return public_ip_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all public IPs."""
        logger.info(f"Scanning public IPs in subscription {self.subscription_id}")
        return self.list_public_ips()


def scan_public_ips(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan public IPs in the subscription."""
    from pathlib import Path
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = PublicIPsScanner(credentials, subscription_id)
    public_ips = scanner.scan()

    if public_ips:
        public_ips = process_resources(public_ips, "azure_public_ip")
        # Generate Terraform files
        generate_tf_auto(public_ips, "azure_public_ip", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(public_ips)} Azure Public IPs")

        # Generate import file
        generate_imports_file(
            "azure_public_ip",
            public_ips,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return public_ips
