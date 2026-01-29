from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_memorystore_redis(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Memorystore Redis instances and generates Terraform code.
    """
    def _scan_redis():
        redis_client = get_gcp_client("redis", "v1")
        print(f"Scanning for Memorystore Redis instances...")
        
        # Get all Redis instances
        redis_instances = []
        # List all locations first
        if region:
            locations = [f"projects/{project_id or redis_client.project}/locations/{region}"]
        else:
            # Get all available locations
            locations_response = redis_client.projects().locations().list(
                name=f"projects/{project_id or redis_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for location in locations:
            try:
                # List instances in each location
                request = redis_client.projects().locations().instances().list(parent=location)
                
                while request is not None:
                    response = request.execute()
                    
                    for instance in response.get('instances', []):
                        # Extract instance details
                        instance_data = {
                            'name': instance['name'].split('/')[-1],
                            'name_sanitized': instance['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'display_name': instance.get('displayName'),
                            'tier': instance.get('tier', 'STANDARD_HA'),
                            'memory_size_gb': instance.get('memorySizeGb'),
                            'region': location.split('/')[-1],
                            'location_id': instance.get('locationId'),
                            'alternative_location_id': instance.get('alternativeLocationId'),
                            'redis_version': instance.get('redisVersion'),
                            'reserved_ip_range': instance.get('reservedIpRange'),
                            'connect_mode': instance.get('connectMode'),
                            'auth_enabled': instance.get('authEnabled'),
                            'transit_encryption_mode': instance.get('transitEncryptionMode'),
                            'authorized_network': instance.get('authorizedNetwork'),
                            'redis_configs': instance.get('redisConfigs', {}),
                            'current_location_id': instance.get('currentLocationId'),
                            'create_time': instance.get('createTime'),
                            'state': instance.get('state'),
                            'status_message': instance.get('statusMessage'),
                            'host': instance.get('host'),
                            'port': instance.get('port'),
                            'persistence_iam_identity': instance.get('persistenceIamIdentity'),
                            'server_ca_certs': instance.get('serverCaCerts', []),
                            'labels': instance.get('labels', {}),
                        }
                        
                        # Handle maintenance policy
                        if instance.get('maintenancePolicy'):
                            maintenance_policy = instance['maintenancePolicy']
                            instance_data['maintenance_policy'] = {
                                'create_time': maintenance_policy.get('createTime'),
                                'update_time': maintenance_policy.get('updateTime'),
                                'description': maintenance_policy.get('description'),
                            }
                            
                            if maintenance_policy.get('weeklyMaintenanceWindow'):
                                windows = maintenance_policy['weeklyMaintenanceWindow']
                                if windows:
                                    window = windows[0]  # Take the first window
                                    instance_data['maintenance_policy']['weekly_maintenance_window'] = {
                                        'day': window.get('day'),
                                        'start_time': window.get('startTime', {})
                                    }
                        
                        # Handle persistence config
                        if instance.get('persistenceConfig'):
                            instance_data['persistence_config'] = {
                                'persistence_mode': instance['persistenceConfig'].get('persistenceMode'),
                                'rdb_snapshot_period': instance['persistenceConfig'].get('rdbSnapshotPeriod'),
                                'rdb_next_snapshot_time': instance['persistenceConfig'].get('rdbNextSnapshotTime'),
                                'rdb_snapshot_start_time': instance['persistenceConfig'].get('rdbSnapshotStartTime'),
                            }
                        
                        redis_instances.append(instance_data)
                    
                    request = redis_client.projects().locations().instances().list_next(
                        previous_request=request, previous_response=response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {location}: {e}")
        
        return redis_instances
    
    # Use safe operation wrapper
    redis_instances = safe_gcp_operation(
        _scan_redis, 
        "Memorystore for Redis API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_memorystore_redis.tf"
    generate_tf(redis_instances, "gcp_memorystore_redis", output_file)
    
    # Only generate imports file and print success message if we have instances
    if redis_instances:
        print(f"Generated Terraform for {len(redis_instances)} Memorystore Redis instances -> {output_file}")
        
        # Generate imports file
        imports = []
        for instance in redis_instances:
            location = instance['region']
            project = project_id or "default"
            imports.append({
                "resource_type": "google_redis_instance",
                "resource_name": instance['name_sanitized'],
                "resource_id": f"projects/{project}/locations/{location}/instances/{instance['name']}"
            })
        
        generate_imports_file(
            "gcp_memorystore_redis",
            redis_instances,
            "name",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(redis_instances)} resources")

def list_memorystore_redis(output_dir: Path):
    """List scanned Memorystore Redis instances."""
    import json
    
    tf_file = output_dir / "gcp_memorystore_redis.tf"
    if not tf_file.exists():
        print("No Memorystore Redis instances found. Run 'scan-redis' first.")
        return
    
    # Read the generated file to extract instance information
    # This is a simplified implementation - in practice, you'd parse the TF file
    print("Scanned Memorystore Redis instances:")
    print(f"  - Check {tf_file} for details")

def import_memorystore_redis(instance_id: str, output_dir: Path):
    """Import a specific Memorystore Redis instance."""
    imports_file = output_dir / "gcp_memorystore_redis_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-redis' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_redis_instance", instance_id)