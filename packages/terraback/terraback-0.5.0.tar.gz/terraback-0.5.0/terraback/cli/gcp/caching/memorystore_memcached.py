from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_memorystore_memcached(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Memorystore Memcached instances and generates Terraform code.
    """
    def _scan_memorystore_memcached():
        memcache_client = get_gcp_client("memcache", "v1")
        
        print(f"Scanning for Memorystore Memcached instances...")
        
        # Get all Memcached instances
        memcached_instances = []
        
        # List all locations first
        if region:
            locations = [f"projects/{project_id or memcache_client.project}/locations/{region}"]
        else:
            # Get all available locations
            locations_response = memcache_client.projects().locations().list(
                name=f"projects/{project_id or memcache_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for location in locations:
            try:
                # List instances in each location
                request = memcache_client.projects().locations().instances().list(parent=location)
                
                while request is not None:
                    response = request.execute()
                    
                    for instance in response.get('instances', []):
                        # Extract instance details
                        instance_data = {
                            'name': instance['name'].split('/')[-1],
                            'name_sanitized': instance['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'display_name': instance.get('displayName'),
                            'node_count': instance.get('nodeCount'),
                            'region': location.split('/')[-1],
                            'zones': instance.get('zones', []),
                            'memcache_version': instance.get('memcacheVersion'),
                            'authorized_network': instance.get('authorizedNetwork'),
                            'state': instance.get('state'),
                            'create_time': instance.get('createTime'),
                            'update_time': instance.get('updateTime'),
                            'memcache_full_version': instance.get('memcacheFullVersion'),
                            'discovery_endpoint': instance.get('discoveryEndpoint'),
                            'labels': instance.get('labels', {}),
                        }
                        
                        # Handle node config
                        if instance.get('nodeConfig'):
                            instance_data['node_config'] = {
                                'cpu_count': instance['nodeConfig'].get('cpuCount'),
                                'memory_size_mb': instance['nodeConfig'].get('memorySizeMb')
                            }
                        
                        # Handle memcache parameters
                        if instance.get('parameters'):
                            instance_data['memcache_parameters'] = {
                                'id': instance['parameters'].get('id'),
                                'params': instance['parameters'].get('params', {})
                            }
                        
                        # Handle instance messages
                        if instance.get('instanceMessages'):
                            instance_data['instance_messages'] = []
                            for msg in instance['instanceMessages']:
                                instance_data['instance_messages'].append({
                                    'code': msg.get('code'),
                                    'message': msg.get('message')
                                })
                        
                        # Handle maintenance policy
                        if instance.get('maintenancePolicy'):
                            maintenance_policy = instance['maintenancePolicy']
                            instance_data['maintenance_policy'] = {
                                'create_time': maintenance_policy.get('createTime'),
                                'update_time': maintenance_policy.get('updateTime'),
                                'description': maintenance_policy.get('description'),
                                'weekly_maintenance_window': []
                            }
                            
                            for window in maintenance_policy.get('weeklyMaintenanceWindow', []):
                                instance_data['maintenance_policy']['weekly_maintenance_window'].append({
                                    'day': window.get('day'),
                                    'duration': window.get('duration'),
                                    'start_time': window.get('startTime', {})
                                })
                        
                        # Handle memcache nodes
                        if instance.get('memcacheNodes'):
                            instance_data['memcache_nodes'] = []
                            for node in instance['memcacheNodes']:
                                instance_data['memcache_nodes'].append({
                                    'node_id': node.get('nodeId'),
                                    'zone': node.get('zone'),
                                    'state': node.get('state'),
                                    'host': node.get('host'),
                                    'port': node.get('port'),
                                    'parameters': node.get('parameters', {})
                                })
                        
                        memcached_instances.append(instance_data)
                    
                    request = memcache_client.projects().locations().instances().list_next(
                        previous_request=request, previous_response=response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {location}: {e}")
        
        return memcached_instances
    
    # Use safe operation wrapper
    memcached_instances = safe_gcp_operation(
        _scan_memorystore_memcached, 
        "Memorystore for Memcached API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_memorystore_memcached.tf"
    generate_tf(memcached_instances, "gcp_memorystore_memcached", output_file)
    
    # Only generate imports file and print success message if we have instances
    if memcached_instances:
        print(f"Generated Terraform for {len(memcached_instances)} Memorystore Memcached instances -> {output_file}")
        
        # Generate imports file
        imports = []
        for instance in memcached_instances:
            location = instance['region']
            project = project_id or "default"
            imports.append({
                "resource_type": "google_memcache_instance",
                "resource_name": instance['name_sanitized'],
                "resource_id": f"projects/{project}/locations/{location}/instances/{instance['name']}"
            })
        
        imports_file = output_dir / "gcp_memorystore_memcached_imports.tf"
        generate_imports_file(imports, imports_file, provider="gcp")
        print(f"Generated imports file -> {imports_file}")

def list_memorystore_memcached(output_dir: Path):
    """List scanned Memorystore Memcached instances."""
    import json
    
    tf_file = output_dir / "gcp_memorystore_memcached.tf"
    if not tf_file.exists():
        print("No Memorystore Memcached instances found. Run 'scan-memcached' first.")
        return
    
    # Read the generated file to extract instance information
    # This is a simplified implementation - in practice, you'd parse the TF file
    print("Scanned Memorystore Memcached instances:")
    print(f"  - Check {tf_file} for details")

def import_memorystore_memcached(instance_id: str, output_dir: Path):
    """Import a specific Memorystore Memcached instance."""
    imports_file = output_dir / "gcp_memorystore_memcached_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-memcached' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_memcache_instance", instance_id)