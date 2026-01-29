from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.redis import RedisManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class RedisCachesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = RedisManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_redis_caches(self) -> List[Dict[str, Any]]:
        """List all Redis caches in the subscription."""
        redis_caches = []
        
        try:
            # List all Redis caches
            for cache in self.client.redis.list_by_subscription():
                try:
                    redis_caches.append(self._process_redis_cache(cache))
                except Exception as e:
                    logger.error(f"Error processing Redis cache {cache.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing Redis caches: {str(e)}")
            
        return redis_caches

    def _process_redis_cache(self, cache) -> Dict[str, Any]:
        """Process a single Redis cache resource."""
        # Normalize the resource ID - Azure returns /Redis/ but Terraform expects /redis/
        normalized_id = cache.id.replace('/Microsoft.Cache/Redis/', '/Microsoft.Cache/redis/')
        
        redis_cache_data = {
            "id": normalized_id,
            "name": cache.name,
            "type": "azure_redis_cache",
            "resource_type": "azure_redis_cache",
            "resource_group_name": cache.id.split('/')[4],
            "location": cache.location,
            "properties": {
                "name": cache.name,
                "location": cache.location,
                "resource_group_name": cache.id.split('/')[4],
                "capacity": cache.sku.capacity,
                "family": cache.sku.family,
                "sku_name": cache.sku.name,
                "enable_non_ssl_port": cache.enable_non_ssl_port,
                "minimum_tls_version": cache.minimum_tls_version,
                "redis_version": cache.redis_version,
                "port": cache.port,
                "ssl_port": cache.ssl_port,
                "host_name": cache.host_name,
                "provisioning_state": cache.provisioning_state,
            }
        }
        
        # Add optional properties
        if cache.public_network_access:
            redis_cache_data["properties"]["public_network_access_enabled"] = (
                cache.public_network_access == "Enabled"
            )
            
        if cache.subnet_id:
            redis_cache_data["properties"]["subnet_id"] = cache.subnet_id
            
        if cache.shard_count:
            redis_cache_data["properties"]["shard_count"] = cache.shard_count
            
        if cache.zones:
            redis_cache_data["properties"]["zones"] = cache.zones
            
        # Process Redis configuration
        if cache.redis_configuration:
            config = {}
            if hasattr(cache.redis_configuration, 'maxmemory_delta'):
                config['maxmemory_delta'] = cache.redis_configuration.maxmemory_delta
            if hasattr(cache.redis_configuration, 'maxmemory_reserved'):
                config['maxmemory_reserved'] = cache.redis_configuration.maxmemory_reserved
            if hasattr(cache.redis_configuration, 'maxmemory_policy'):
                config['maxmemory_policy'] = cache.redis_configuration.maxmemory_policy
            if hasattr(cache.redis_configuration, 'rdb_backup_enabled'):
                config['rdb_backup_enabled'] = cache.redis_configuration.rdb_backup_enabled
            if hasattr(cache.redis_configuration, 'rdb_backup_frequency'):
                config['rdb_backup_frequency'] = cache.redis_configuration.rdb_backup_frequency
            if hasattr(cache.redis_configuration, 'rdb_backup_max_snapshot_count'):
                config['rdb_backup_max_snapshot_count'] = cache.redis_configuration.rdb_backup_max_snapshot_count
            if hasattr(cache.redis_configuration, 'rdb_storage_connection_string'):
                config['rdb_storage_connection_string'] = cache.redis_configuration.rdb_storage_connection_string
                
            if config:
                redis_cache_data["properties"]["redis_configuration"] = config
        
        # Process patch schedules
        try:
            patch_schedules = list(self.client.patch_schedules.list_by_redis_resource(
                resource_group_name=redis_cache_data["resource_group_name"],
                name=cache.name
            ))
            if patch_schedules:
                schedules = []
                for schedule in patch_schedules:
                    if schedule.schedule_entries:
                        for entry in schedule.schedule_entries:
                            schedule_data = {
                                "day_of_week": entry.day_of_week,
                                "start_hour_utc": entry.start_hour_utc
                            }
                            if entry.maintenance_window:
                                schedule_data["maintenance_window"] = entry.maintenance_window
                            schedules.append(schedule_data)
                if schedules:
                    redis_cache_data["properties"]["patch_schedule"] = schedules
        except Exception as e:
            logger.debug(f"Could not retrieve patch schedules for {cache.name}: {str(e)}")
        
        # Add tags
        if cache.tags:
            redis_cache_data["properties"]["tags"] = cache.tags
            
        return redis_cache_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all Redis caches."""
        logger.info(f"Scanning Redis caches in subscription {self.subscription_id}")
        return self.list_redis_caches()


@require_professional
def scan_redis_caches(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Redis Caches in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = RedisCachesScanner(credentials, subscription_id)
    redis_caches = scanner.scan()
    
    if redis_caches:    # Process resources before generation
        redis_caches = process_resources(redis_caches, "azure_redis_cache")
    

        # Generate Terraform files
        generate_tf_auto(redis_caches, "azure_redis_cache", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(redis_caches)} Azure Redis Caches")
        
        # Generate import file
        generate_imports_file(
            "azure_redis_cache",
            redis_caches,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return redis_caches
