from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_bigtable_instances(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Bigtable instances and generates Terraform code.
    """
    def _scan_bigtable_instances():
        bigtable_client = get_gcp_client("bigtableadmin", "v2")
        
        print(f"Scanning for Bigtable instances...")
        
        # Get all Bigtable instances
        instances = []
        # List instances
        parent = f"projects/{project_id or bigtable_client.project}"
        request = bigtable_client.projects().instances().list(parent=parent)
        
        while request is not None:
            response = request.execute()
            
            for instance in response.get('instances', []):
                # Extract instance details
                instance_data = {
                    'name': instance['name'].split('/')[-1],
                    'name_sanitized': instance['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                    'display_name': instance.get('displayName'),
                    'state': instance.get('state'),
                    'type': instance.get('type'),
                    'labels': instance.get('labels', {}),
                    'create_time': instance.get('createTime'),
                    'update_time': instance.get('updateTime'),
                    'clusters': []
                }
                
                # Get clusters for this instance
                try:
                    clusters_request = bigtable_client.projects().instances().clusters().list(
                        parent=instance['name']
                    )
                    
                    while clusters_request is not None:
                        clusters_response = clusters_request.execute()
                        
                        for cluster in clusters_response.get('clusters', []):
                            cluster_data = {
                                'cluster_id': cluster['name'].split('/')[-1],
                                'zone': cluster.get('location', '').split('/')[-1],
                                'serve_nodes': cluster.get('serveNodes'),
                                'state': cluster.get('state'),
                                'storage_type': cluster.get('defaultStorageType'),
                                'kms_key_name': cluster.get('encryptionConfig', {}).get('kmsKeyName'),
                            }
                            
                            # Handle autoscaling config
                            if cluster.get('clusterConfig', {}).get('clusterAutoscalingConfig'):
                                autoscaling = cluster['clusterConfig']['clusterAutoscalingConfig']
                                cluster_data['autoscaling_config'] = {
                                    'min_nodes': autoscaling.get('autoscalingLimits', {}).get('minServeNodes'),
                                    'max_nodes': autoscaling.get('autoscalingLimits', {}).get('maxServeNodes'),
                                    'cpu_target': autoscaling.get('autoscalingTargets', {}).get('cpuUtilizationPercent'),
                                    'storage_target': autoscaling.get('autoscalingTargets', {}).get('storageUtilizationGibPerNode')
                                }
                            
                            instance_data['clusters'].append(cluster_data)
                        
                        clusters_request = bigtable_client.projects().instances().clusters().list_next(
                            previous_request=clusters_request, previous_response=clusters_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not get clusters for instance {instance['name']}: {e}")
                
                # Get tables for this instance
                try:
                    tables_request = bigtable_client.projects().instances().tables().list(
                        parent=instance['name']
                    )
                    
                    instance_data['tables'] = []
                    while tables_request is not None:
                        tables_response = tables_request.execute()
                        
                        for table in tables_response.get('tables', []):
                            table_data = {
                                'name': table['name'].split('/')[-1],
                                'name_sanitized': table['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                'column_families': {},
                                'granularity': table.get('granularity'),
                                'restore_info': table.get('restoreInfo'),
                                'change_stream_retention': table.get('changeStreamConfig', {}).get('retentionPeriod'),
                                'deletion_protection': table.get('deletionProtection'),
                                'automated_backup_policy': table.get('automatedBackupPolicy'),
                            }
                            
                            # Get column families
                            if table.get('columnFamilies'):
                                for cf_name, cf_data in table['columnFamilies'].items():
                                    table_data['column_families'][cf_name] = {
                                        'gc_rule': cf_data.get('gcRule')
                                    }
                            
                            instance_data['tables'].append(table_data)
                        
                        tables_request = bigtable_client.projects().instances().tables().list_next(
                            previous_request=tables_request, previous_response=tables_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not get tables for instance {instance['name']}: {e}")
                
                # Get app profiles for this instance
                try:
                    app_profiles_request = bigtable_client.projects().instances().appProfiles().list(
                        parent=instance['name']
                    )
                    
                    instance_data['app_profiles'] = []
                    while app_profiles_request is not None:
                        app_profiles_response = app_profiles_request.execute()
                        
                        for profile in app_profiles_response.get('appProfiles', []):
                            profile_data = {
                                'app_profile_id': profile['name'].split('/')[-1],
                                'name_sanitized': profile['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                'description': profile.get('description'),
                                'etag': profile.get('etag'),
                            }
                            
                            # Handle routing policy
                            if profile.get('multiClusterRoutingUseAny'):
                                profile_data['multi_cluster_routing_use_any'] = True
                                profile_data['single_cluster_routing'] = None
                            elif profile.get('singleClusterRouting'):
                                profile_data['multi_cluster_routing_use_any'] = False
                                profile_data['single_cluster_routing'] = {
                                    'cluster_id': profile['singleClusterRouting'].get('clusterId'),
                                    'allow_transactional_writes': profile['singleClusterRouting'].get('allowTransactionalWrites', False)
                                }
                            
                            instance_data['app_profiles'].append(profile_data)
                        
                        app_profiles_request = bigtable_client.projects().instances().appProfiles().list_next(
                            previous_request=app_profiles_request, previous_response=app_profiles_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not get app profiles for instance {instance['name']}: {e}")
                
                instances.append(instance_data)
            
            request = bigtable_client.projects().instances().list_next(
                previous_request=request, previous_response=response
            )
    
        return instances
    
    # Use safe operation wrapper
    instances = safe_gcp_operation(
        _scan_bigtable_instances, 
        "Cloud Bigtable Admin API", 
        project_id or "default"
    )
    
    if not instances:
        print(f"Skipping gcp_bigtable_instance - no resources found")
        return
    
    output_file = output_dir / "gcp_bigtable_instance.tf"
    generate_tf(instances, "gcp_bigtable_instance", output_file)
    print(f"Generated Terraform for {len(instances)} Bigtable instances -> {output_file}")
    
    # Generate imports file
    imports = []
    for instance in instances:
        project = project_id or "default"
        imports.append({
            "resource_type": "google_bigtable_instance",
            "resource_name": instance['name_sanitized'],
            "resource_id": f"projects/{project}/instances/{instance['name']}"
        })
        
        # Add imports for tables
        for table in instance.get('tables', []):
            imports.append({
                "resource_type": "google_bigtable_table",
                "resource_name": f"{instance['name_sanitized']}_{table['name_sanitized']}",
                "resource_id": f"{instance['name']}!{table['name']}"
            })
        
        # Add imports for app profiles
        for profile in instance.get('app_profiles', []):
            imports.append({
                "resource_type": "google_bigtable_app_profile",
                "resource_name": f"{instance['name_sanitized']}_{profile['name_sanitized']}",
                "resource_id": f"{instance['name']}/{profile['app_profile_id']}"
            })
    
    if instances:
        generate_imports_file(
            "gcp_bigtable_instance",
            instances,
            "name",
            output_dir,
            provider="gcp"
        )

def list_bigtable_instances(output_dir: Path):
    """List scanned Bigtable instances."""
    tf_file = output_dir / "gcp_bigtable_instance.tf"
    if not tf_file.exists():
        print("No Bigtable instances found. Run 'scan-bigtable' first.")
        return
    
    print("Scanned Bigtable instances:")
    print(f"  - Check {tf_file} for details")

def import_bigtable_instance(instance_id: str, output_dir: Path):
    """Import a specific Bigtable instance."""
    imports_file = output_dir / "gcp_bigtable_instance_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-bigtable' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_bigtable_instance", instance_id)