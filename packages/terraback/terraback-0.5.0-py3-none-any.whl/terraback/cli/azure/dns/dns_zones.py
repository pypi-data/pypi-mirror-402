from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional
from terraback.cli.azure.common.utils import normalize_resource_id

logger = get_logger(__name__)


class DnsZonesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = DnsManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_dns_zones(self) -> List[Dict[str, Any]]:
        """List all DNS zones in the subscription."""
        dns_zones = []
        
        try:
            # List all DNS zones
            for zone in self.client.zones.list():
                try:
                    dns_zones.append(self._process_dns_zone(zone))
                except Exception as e:
                    logger.error(f"Error processing DNS zone {zone.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing DNS zones: {str(e)}")
            
        return dns_zones

    def _process_dns_zone(self, zone) -> Dict[str, Any]:
        """Process a single DNS zone resource."""
        # Normalize the resource ID
        normalized_id = normalize_resource_id(zone.id)
        
        dns_zone_data = {
            "id": normalized_id,
            "name": zone.name,
            "type": "azure_dns_zone",
            "resource_type": "azure_dns_zone",
            "resource_group_name": normalized_id.split('/')[4],
            "properties": {
                "name": zone.name,
                "resource_group_name": normalized_id.split('/')[4],
            }
        }
        
        # Add SOA record if available
        if hasattr(zone, 'soa_record') and zone.soa_record:
            soa = zone.soa_record
            dns_zone_data["properties"]["soa_record"] = {
                "email": soa.email,
                "expire_time": soa.expire_time,
                "minimum_ttl": soa.minimum_ttl,
                "refresh_time": soa.refresh_time,
                "retry_time": soa.retry_time,
                "ttl": soa.ttl
            }
            if hasattr(soa, 'host'):
                dns_zone_data["properties"]["soa_record"]["host_name"] = soa.host
        
        # Add other properties
        if hasattr(zone, 'number_of_record_sets'):
            dns_zone_data["properties"]["number_of_record_sets"] = zone.number_of_record_sets
            
        if hasattr(zone, 'max_number_of_record_sets'):
            dns_zone_data["properties"]["max_number_of_record_sets"] = zone.max_number_of_record_sets
            
        if hasattr(zone, 'name_servers') and zone.name_servers:
            dns_zone_data["properties"]["name_servers"] = zone.name_servers
        
        # Add tags
        if zone.tags:
            dns_zone_data["properties"]["tags"] = zone.tags
            
        return dns_zone_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all DNS zones."""
        logger.info(f"Scanning DNS zones in subscription {self.subscription_id}")
        return self.list_dns_zones()


@require_professional
def scan_dns_zones(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan DNS Zones in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = DnsZonesScanner(credentials, subscription_id)
    dns_zones = scanner.scan()
    
    if dns_zones:
        # Generate Terraform files
        generate_tf_auto(dns_zones, "azure_dns_zone", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(dns_zones)} Azure DNS Zones")
        
        # Generate import file
        generate_imports_file(
            "azure_dns_zone",
            dns_zones,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return dns_zones
