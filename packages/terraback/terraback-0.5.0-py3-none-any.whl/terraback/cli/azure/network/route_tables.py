from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result

logger = get_logger(__name__)


class RouteTablesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = NetworkManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_route_tables(self) -> List[Dict[str, Any]]:
        """List all route tables in the subscription."""
        route_tables = []
        
        try:
            # List all route tables
            for route_table in self.client.route_tables.list_all():
                try:
                    route_tables.append(self._process_route_table(route_table))
                except Exception as e:
                    logger.error(f"Error processing route table {route_table.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing route tables: {str(e)}")
            
        return route_tables

    def _process_route_table(self, route_table) -> Dict[str, Any]:
        """Process a single route table resource."""
        route_table_data = {
            "id": route_table.id,
            "name": route_table.name,
            "type": "azure_route_table",
            "resource_type": "azure_route_table",
            "resource_group_name": route_table.id.split('/')[4],
            "location": route_table.location,
            "properties": {
                "name": route_table.name,
                "location": route_table.location,
                "resource_group_name": route_table.id.split('/')[4],
            }
        }
        
        # Add BGP route propagation setting
        if hasattr(route_table, 'disable_bgp_route_propagation') and route_table.disable_bgp_route_propagation is not None:
            route_table_data["properties"]["disable_bgp_route_propagation"] = route_table.disable_bgp_route_propagation
        
        # Process routes
        if route_table.routes:
            routes = []
            for route in route_table.routes:
                route_data = {
                    "name": route.name,
                    "address_prefix": route.address_prefix,
                    "next_hop_type": route.next_hop_type,
                }
                if route.next_hop_ip_address:
                    route_data["next_hop_in_ip_address"] = route.next_hop_ip_address
                routes.append(route_data)
            route_table_data["properties"]["routes"] = routes
        
        # Add associated subnets info
        if hasattr(route_table, 'subnets') and route_table.subnets:
            route_table_data["properties"]["subnet_ids"] = [subnet.id for subnet in route_table.subnets]
        
        # Add tags
        if route_table.tags:
            route_table_data["properties"]["tags"] = route_table.tags
            
        return route_table_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all route tables."""
        logger.info(f"Scanning route tables in subscription {self.subscription_id}")
        return self.list_route_tables()


def scan_route_tables(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure Route Tables in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = RouteTablesScanner(credentials, subscription_id)
    route_tables = scanner.scan()
    
    if route_tables:    # Process resources before generation
        route_tables = process_resources(route_tables, "azure_route_table")
    

        # Generate Terraform files
        generate_tf_auto(route_tables, "azure_route_table", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(route_tables)} Azure Route Tables")
        
        # Generate import file
        generate_imports_file(
            "azure_route_table",
            route_tables,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return route_tables
