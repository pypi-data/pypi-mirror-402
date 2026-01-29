from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_firestore_databases(output_dir: Path, project_id: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Firestore databases and generates Terraform code.
    """
    def _scan_firestore_databases():
        firestore_client = get_gcp_client("firestore", "v1")
        
        print(f"Scanning for Firestore databases...")
        
        # Get all Firestore databases
        databases = []
        # List databases
        parent = f"projects/{project_id or firestore_client.project}"
        request = firestore_client.projects().databases().list(parent=parent)
        
        while request is not None:
            response = request.execute()
            
            for database in response.get('databases', []):
                # Extract database details
                database_data = {
                    'name': database['name'].split('/')[-1],
                    'name_sanitized': database['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                    'location_id': database.get('locationId'),
                    'type': database.get('type', 'FIRESTORE_NATIVE'),
                    'concurrency_mode': database.get('concurrencyMode'),
                    'app_engine_integration_mode': database.get('appEngineIntegrationMode'),
                    'key_prefix': database.get('keyPrefix'),
                    'delete_protection_state': database.get('deleteProtectionState'),
                    'point_in_time_recovery_enablement': database.get('pointInTimeRecoveryEnablement'),
                    'version_retention_period': database.get('versionRetentionPeriod'),
                    'earliest_version_time': database.get('earliestVersionTime'),
                    'create_time': database.get('createTime'),
                    'update_time': database.get('updateTime'),
                    'etag': database.get('etag'),
                    'uid': database.get('uid'),
                    'labels': database.get('labels', {}),
                }
                
                # Get indexes for this database
                try:
                    indexes_parent = database['name']
                    indexes_request = firestore_client.projects().databases().collectionGroups().indexes().list(
                        parent=f"{indexes_parent}/collectionGroups/-"
                    )
                    
                    database_data['indexes'] = []
                    while indexes_request is not None:
                        indexes_response = indexes_request.execute()
                        
                        for index in indexes_response.get('indexes', []):
                            if index.get('state') == 'READY':  # Only include ready indexes
                                index_data = {
                                    'name': index['name'].split('/')[-1],
                                    'collection': index['name'].split('/collectionGroups/')[1].split('/')[0],
                                    'query_scope': index.get('queryScope'),
                                    'api_scope': index.get('apiScope'),
                                    'fields': []
                                }
                                
                                for field in index.get('fields', []):
                                    field_data = {
                                        'field_path': field.get('fieldPath')
                                    }
                                    if field.get('order'):
                                        field_data['order'] = field['order']
                                    if field.get('arrayConfig'):
                                        field_data['array_config'] = field['arrayConfig']
                                    index_data['fields'].append(field_data)
                                
                                database_data['indexes'].append(index_data)
                        
                        indexes_request = firestore_client.projects().databases().collectionGroups().indexes().list_next(
                            previous_request=indexes_request, previous_response=indexes_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not get indexes for database {database['name']}: {e}")
                
                databases.append(database_data)
            
            request = firestore_client.projects().databases().list_next(
                previous_request=request, previous_response=response
            )
        
        return databases
    
    # Use safe operation wrapper
    databases = safe_gcp_operation(
        _scan_firestore_databases, 
        "Cloud Firestore API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_firestore_database.tf"
    generate_tf(databases, "gcp_firestore_database", output_file)
    print(f"Generated Terraform for {len(databases)} Firestore databases -> {output_file}")
    
    # Generate imports file
    imports = []
    for database in databases:
        project = project_id or "default"
        imports.append({
            "resource_type": "google_firestore_database",
            "resource_name": database['name_sanitized'],
            "resource_id": f"projects/{project}/databases/{database['name']}"
        })
        
        # Add imports for indexes
        for idx, index in enumerate(database.get('indexes', [])):
            imports.append({
                "resource_type": "google_firestore_index",
                "resource_name": f"{database['name_sanitized']}_{idx + 1}",
                "resource_id": f"projects/{project}/databases/{database['name']}/collectionGroups/{index['collection']}/indexes/{index['name']}"
            })
    
    if databases:
        generate_imports_file(
            "gcp_firestore_database",
            databases,
            "name",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(databases)} resources")

def list_firestore_databases(output_dir: Path):
    """List scanned Firestore databases."""
    tf_file = output_dir / "gcp_firestore_database.tf"
    if not tf_file.exists():
        print("No Firestore databases found. Run 'scan-firestore' first.")
        return
    
    print("Scanned Firestore databases:")
    print(f"  - Check {tf_file} for details")

def import_firestore_database(database_id: str, output_dir: Path):
    """Import a specific Firestore database."""
    imports_file = output_dir / "gcp_firestore_database_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-firestore' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_firestore_database", database_id)