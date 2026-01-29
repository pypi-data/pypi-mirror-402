from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.dns import DnsManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional
from terraback.cli.azure.resource_processor import process_resources
from terraback.cli.azure.common.utils import sanitize_resource_name, normalize_resource_id

logger = get_logger(__name__)


class DnsRecordsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = DnsManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_dns_records(self) -> List[Dict[str, Any]]:
        """List all DNS records in the subscription."""
        dns_records = []
        
        try:
            # First get all zones
            for zone in self.client.zones.list():
                resource_group_name = zone.id.split('/')[4]
                
                # Then get all record sets for each zone
                try:
                    for record_set in self.client.record_sets.list_by_dns_zone(
                        resource_group_name=resource_group_name,
                        zone_name=zone.name
                    ):
                        # Skip SOA and NS records at zone apex as they're managed by the zone
                        if record_set.name == "@" and record_set.type in ["SOA", "NS"]:
                            continue
                            
                        try:
                            record_data = self._process_dns_record(record_set, zone.name, resource_group_name)
                            if record_data:
                                dns_records.append(record_data)
                        except Exception as e:
                            logger.error(f"Error processing DNS record {record_set.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.error(f"Error listing records for zone {zone.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing DNS zones: {str(e)}")

        dns_records = process_resources(dns_records, "azure_dns_record")
        return dns_records

    def _process_dns_record(self, record_set, zone_name: str, resource_group_name: str) -> Optional[Dict[str, Any]]:
        """Process a single DNS record set."""
        # Extract record type from the type field (e.g., "Microsoft.Network/dnszones/A" -> "A")
        record_type = record_set.type.split('/')[-1]
        
        # Skip unsupported record types
        if record_type not in ["A", "AAAA", "CAA", "CNAME", "MX", "NS", "PTR", "SRV", "TXT"]:
            return None
        
        # Create a sanitized name for the Terraform resource
        record_name = f"{record_set.name}_{zone_name.replace('.', '_')}_{record_type}"
        sanitized_name = sanitize_resource_name(record_name)
        
        dns_record_data = {
            "id": normalize_resource_id(record_set.id),
            "name": record_name,
            "name_sanitized": sanitized_name,
            "type": f"azure_dns_{record_type.lower()}_record",
            "resource_type": f"azure_dns_{record_type.lower()}_record",
            "resource_group_name": resource_group_name,
            "properties": {
                "name": record_set.name,
                "zone_name": zone_name,
                "resource_group_name": resource_group_name,
                "ttl": record_set.ttl,
                "record_type": record_type
            }
        }
        
        # Process records based on type
        if record_type == "A" and record_set.a_records:
            dns_record_data["properties"]["records"] = [r.ipv4_address for r in record_set.a_records]
            
        elif record_type == "AAAA" and record_set.aaaa_records:
            dns_record_data["properties"]["records"] = [r.ipv6_address for r in record_set.aaaa_records]
            
        elif record_type == "CAA" and record_set.caa_records:
            dns_record_data["properties"]["records"] = [
                {
                    "flags": r.flags,
                    "tag": r.tag,
                    "value": r.value
                } for r in record_set.caa_records
            ]
            
        elif record_type == "CNAME" and record_set.cname_record:
            dns_record_data["properties"]["record"] = record_set.cname_record.cname
            
        elif record_type == "MX" and record_set.mx_records:
            dns_record_data["properties"]["records"] = [
                {
                    "preference": r.preference,
                    "exchange": r.exchange
                } for r in record_set.mx_records
            ]
            
        elif record_type == "NS" and record_set.ns_records:
            dns_record_data["properties"]["records"] = [r.nsdname for r in record_set.ns_records]
            
        elif record_type == "PTR" and record_set.ptr_records:
            dns_record_data["properties"]["records"] = [r.ptrdname for r in record_set.ptr_records]
            
        elif record_type == "SRV" and record_set.srv_records:
            dns_record_data["properties"]["records"] = [
                {
                    "priority": r.priority,
                    "weight": r.weight,
                    "port": r.port,
                    "target": r.target
                } for r in record_set.srv_records
            ]
            
        elif record_type == "TXT" and record_set.txt_records:
            dns_record_data["properties"]["records"] = [
                {"value": " ".join(r.value)} for r in record_set.txt_records
            ]
        
        # Add target resource ID if it's an alias record
        if hasattr(record_set, 'target_resource') and record_set.target_resource:
            dns_record_data["properties"]["target_resource_id"] = record_set.target_resource.id
        
        # Add metadata
        if hasattr(record_set, 'metadata') and record_set.metadata:
            dns_record_data["properties"]["tags"] = record_set.metadata
            
        return dns_record_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all DNS records."""
        logger.info(f"Scanning DNS records in subscription {self.subscription_id}")
        return self.list_dns_records()


@require_professional
def scan_dns_records(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan DNS Records in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = DnsRecordsScanner(credentials, subscription_id)
    dns_records = scanner.scan()

    if dns_records:
        # Group records by their specific resource type first
        records_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for record in dns_records:
            resource_type = record.get("resource_type")
            if not resource_type:
                continue
            records_by_type.setdefault(resource_type, []).append(record)

        # Generate separate .tf files and import files for each DNS record type
        total_records = 0
        for resource_type, resources in records_by_type.items():
            # Generate .tf file for this specific DNS record type
            generate_tf_auto(resources, resource_type, output_dir)
            total_records += len(resources)
            
            # Generate import file for this specific DNS record type
            generate_imports_file(
                resource_type,
                resources,
                remote_resource_id_key="id",
                output_dir=output_dir,
                provider="azure",
            )
        
        print(f"[Cross-scan] Generated Terraform for {total_records} Azure DNS Records across {len(records_by_type)} types")

    return dns_records
