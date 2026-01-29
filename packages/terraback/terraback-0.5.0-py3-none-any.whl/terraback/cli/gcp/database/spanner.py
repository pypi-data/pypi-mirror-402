from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_spanner_instances(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Spanner instances and generates Terraform code.
    """
    def _scan_spanner_instances():
        spanner_client = get_gcp_client("spanner", "v1")
        
        print(f"Scanning for Spanner instances...")
        
        # Get all Spanner instances
        instances = []
        # List instances
        parent = f"projects/{project_id or spanner_client.project}"
        request = spanner_client.projects().instances().list(parent=parent)
        
        while request is not None:
            response = request.execute()
            
            for instance in response.get('instances', []):
                # Extract instance details
                instance_data = {
                    'name': instance['name'].split('/')[-1],
                    'name_sanitized': instance['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                    'config': instance.get('config'),
                    'display_name': instance.get('displayName'),
                    'node_count': instance.get('nodeCount'),
                    'processing_units': instance.get('processingUnits'),
                    'state': instance.get('state'),
                    'labels': instance.get('labels', {}),
                    'endpoint_uris': instance.get('endpointUris', []),
                    'create_time': instance.get('createTime'),
                    'update_time': instance.get('updateTime'),
                }
                
                # Handle autoscaling config
                if instance.get('autoscalingConfig'):
                    autoscaling = instance['autoscalingConfig']
                    instance_data['autoscaling_config'] = {
                        'autoscaling_limits': {},
                        'autoscaling_targets': {}
                    }
                    
                    if autoscaling.get('autoscalingLimits'):
                        limits = autoscaling['autoscalingLimits']
                        instance_data['autoscaling_config']['autoscaling_limits'] = {
                            'min_processing_units': limits.get('minProcessingUnits'),
                            'max_processing_units': limits.get('maxProcessingUnits'),
                            'min_nodes': limits.get('minNodes'),
                            'max_nodes': limits.get('maxNodes'),
                        }
                    
                    if autoscaling.get('autoscalingTargets'):
                        targets = autoscaling['autoscalingTargets']
                        instance_data['autoscaling_config']['autoscaling_targets'] = {
                            'high_priority_cpu_utilization_percent': targets.get('highPriorityCpuUtilizationPercent'),
                            'storage_utilization_percent': targets.get('storageUtilizationPercent'),
                        }
                
                # Get databases for this instance
                try:
                    databases_request = spanner_client.projects().instances().databases().list(
                        parent=instance['name']
                    )
                    
                    instance_data['databases'] = []
                    while databases_request is not None:
                        databases_response = databases_request.execute()
                        
                        for database in databases_response.get('databases', []):
                            database_data = {
                                'name': database['name'].split('/')[-1],
                                'name_sanitized': database['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                'state': database.get('state'),
                                'version_retention_period': database.get('versionRetentionPeriod'),
                                'earliest_version_time': database.get('earliestVersionTime'),
                                'create_time': database.get('createTime'),
                                'restore_info': database.get('restoreInfo'),
                                'encryption_config': database.get('encryptionConfig'),
                                'encryption_info': database.get('encryptionInfo'),
                                'default_leader': database.get('defaultLeader'),
                                'database_dialect': database.get('databaseDialect'),
                                'enable_drop_protection': database.get('enableDropProtection'),
                                'deletion_protection': database.get('deletionProtection'),
                            }
                            
                            # Get DDL statements for the database
                            try:
                                ddl_response = spanner_client.projects().instances().databases().getDdl(
                                    database=database['name']
                                ).execute()
                                
                                database_data['ddl'] = ddl_response.get('statements', [])
                            except Exception as e:
                                print(f"    - Warning: Could not get DDL for database {database['name']}: {e}")
                                database_data['ddl'] = []
                            
                            instance_data['databases'].append(database_data)
                        
                        databases_request = spanner_client.projects().instances().databases().list_next(
                            previous_request=databases_request, previous_response=databases_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not get databases for instance {instance['name']}: {e}")
                
                # Get IAM policy for the instance
                try:
                    iam_response = spanner_client.projects().instances().getIamPolicy(
                        resource=instance['name']
                    ).execute()
                    
                    instance_data['iam_bindings'] = []
                    for binding in iam_response.get('bindings', []):
                        instance_data['iam_bindings'].append({
                            'role': binding['role'],
                            'members': binding['members']
                        })
                except Exception as e:
                    print(f"  - Warning: Could not get IAM policy for instance {instance['name']}: {e}")
                
                instances.append(instance_data)
            
            request = spanner_client.projects().instances().list_next(
                previous_request=request, previous_response=response
            )
    
        return instances
    
    # Use safe operation wrapper
    instances = safe_gcp_operation(
        _scan_spanner_instances, 
        "Cloud Spanner API", 
        project_id or "default"
    )
    
    if not instances:
        print(f"Skipping gcp_spanner_instance - no resources found")
        return

    output_file = output_dir / "gcp_spanner_instance.tf"
    generate_tf(instances, "gcp_spanner_instance", output_file)
    print(f"Generated Terraform for {len(instances)} Spanner instances -> {output_file}")
    
    # Generate imports file
    imports = []
    for instance in instances:
        project = project_id or "default"
        imports.append({
            "resource_type": "google_spanner_instance",
            "resource_name": instance['name_sanitized'],
            "resource_id": instance['name']
        })
        
        # Add imports for databases
        for database in instance.get('databases', []):
            imports.append({
                "resource_type": "google_spanner_database",
                "resource_name": f"{instance['name_sanitized']}_{database['name_sanitized']}",
                "resource_id": f"{instance['name']}/{database['name']}"
            })
        
        # Add imports for IAM bindings
        for idx, binding in enumerate(instance.get('iam_bindings', [])):
            imports.append({
                "resource_type": "google_spanner_instance_iam_binding",
                "resource_name": f"{instance['name_sanitized']}_{idx + 1}",
                "resource_id": f"{instance['name']} {binding['role']}"
            })
    
    generate_imports_file(
        "gcp_spanner_instance",
        instances,
        "name",
        output_dir,
        provider="gcp"
    )

def list_spanner_instances(output_dir: Path):
    """List scanned Spanner instances."""
    tf_file = output_dir / "gcp_spanner_instance.tf"
    if not tf_file.exists():
        print("No Spanner instances found. Run 'scan-spanner' first.")
        return
    
    print("Scanned Spanner instances:")
    print(f"  - Check {tf_file} for details")

def import_spanner_instance(instance_id: str, output_dir: Path):
    """Import a specific Spanner instance."""
    imports_file = output_dir / "gcp_spanner_instance_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-spanner' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_spanner_instance", instance_id)