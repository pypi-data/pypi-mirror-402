from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result

logger = get_logger(__name__)


class NatGatewaysScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = NetworkManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_nat_gateways(self) -> List[Dict[str, Any]]:
        """List all NAT gateways in the subscription."""
        nat_gateways = []
        
        try:
            # List all NAT gateways
            for nat_gateway in self.client.nat_gateways.list_all():
                try:
                    nat_gateways.append(self._process_nat_gateway(nat_gateway))
                except Exception as e:
                    logger.error(f"Error processing NAT gateway {nat_gateway.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing NAT gateways: {str(e)}")
            
        return nat_gateways

    def _process_nat_gateway(self, nat_gateway) -> Dict[str, Any]:
        """Process a single NAT gateway resource."""
        nat_gateway_data = {
            "id": nat_gateway.id,
            "name": nat_gateway.name,
            "type": "azure_nat_gateway",
            "resource_type": "azure_nat_gateway",
            "resource_group_name": nat_gateway.id.split('/')[4],
            "location": nat_gateway.location,
            "properties": {
                "name": nat_gateway.name,
                "location": nat_gateway.location,
                "resource_group_name": nat_gateway.id.split('/')[4],
            }
        }
        
        # Add SKU
        if nat_gateway.sku:
            nat_gateway_data["properties"]["sku_name"] = nat_gateway.sku.name
        
        # Add idle timeout
        if hasattr(nat_gateway, 'idle_timeout_in_minutes') and nat_gateway.idle_timeout_in_minutes:
            nat_gateway_data["properties"]["idle_timeout_in_minutes"] = nat_gateway.idle_timeout_in_minutes
        
        # Add zones
        if nat_gateway.zones:
            nat_gateway_data["properties"]["zones"] = nat_gateway.zones
        
        # Add associated public IPs and prefixes info
        if hasattr(nat_gateway, 'public_ip_addresses') and nat_gateway.public_ip_addresses:
            nat_gateway_data["properties"]["public_ip_address_ids"] = [ip.id for ip in nat_gateway.public_ip_addresses]
            
        if hasattr(nat_gateway, 'public_ip_prefixes') and nat_gateway.public_ip_prefixes:
            nat_gateway_data["properties"]["public_ip_prefix_ids"] = [prefix.id for prefix in nat_gateway.public_ip_prefixes]
            
        # Add associated subnets info
        if hasattr(nat_gateway, 'subnets') and nat_gateway.subnets:
            nat_gateway_data["properties"]["subnet_ids"] = [subnet.id for subnet in nat_gateway.subnets]
        
        # Add tags
        if nat_gateway.tags:
            nat_gateway_data["properties"]["tags"] = nat_gateway.tags
            
        return nat_gateway_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all NAT gateways."""
        logger.info(f"Scanning NAT gateways in subscription {self.subscription_id}")
        return self.list_nat_gateways()


def scan_nat_gateways(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure NAT Gateways in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = NatGatewaysScanner(credentials, subscription_id)
    nat_gateways = scanner.scan()
    
    if nat_gateways:    # Process resources before generation
        nat_gateways = process_resources(nat_gateways, "azure_nat_gateway")
        
        # Generate Terraform files
        generate_tf_auto(nat_gateways, "azure_nat_gateway", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(nat_gateways)} Azure NAT Gateways")
        
        # Generate import file
        generate_imports_file(
            "azure_nat_gateway",
            nat_gateways,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return nat_gateways
