from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_kms_key_rings(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for KMS key rings and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_kms_key_rings():
        kms_client = get_gcp_client("cloudkms", "v1")
        
        print(f"Scanning for KMS key rings...")
        
        # Get all key rings
        key_rings = []
        # List all locations first
        if location:
            locations = [f"projects/{project_id or kms_client.project}/locations/{location}"]
        else:
            # Get all available locations
            locations_response = kms_client.projects().locations().list(
                name=f"projects/{project_id or kms_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for loc in locations:
            try:
                # List key rings in each location
                request = kms_client.projects().locations().keyRings().list(parent=loc)
                
                while request is not None:
                    response = request.execute()
                    
                    for key_ring in response.get('keyRings', []):
                        # Extract key ring details
                        key_ring_data = {
                            'name': key_ring['name'].split('/')[-1],
                            'name_sanitized': key_ring['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                            'location': loc.split('/')[-1],
                            'create_time': key_ring.get('createTime'),
                            'labels': key_ring.get('labels', {}),
                        }
                        
                        key_rings.append(key_ring_data)
                    
                    request = kms_client.projects().locations().keyRings().list_next(
                        previous_request=request, previous_response=response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
        
        return key_rings
    
    # Use safe operation wrapper
    key_rings = safe_gcp_operation(
        _scan_kms_key_rings, 
        "Cloud KMS API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_kms_key_ring.tf"
    generate_tf(key_rings, "gcp_kms_key_ring", output_file)
    print(f"Generated Terraform for {len(key_rings)} KMS key rings -> {output_file}")
    
    # Generate imports file
    imports = []
    for key_ring in key_rings:
        location = key_ring['location']
        project = project_id or "default"
        imports.append({
            "resource_type": "google_kms_key_ring",
            "resource_name": key_ring['name_sanitized'],
            "resource_id": f"projects/{project}/locations/{location}/keyRings/{key_ring['name']}"
        })
    
    if key_rings:
        generate_imports_file(
            "gcp_kms_key_ring",
            key_rings,
            "name",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(key_rings)} resources")

def scan_kms_crypto_keys(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for KMS crypto keys and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
    
    def _scan_kms_crypto_keys():
        kms_client = get_gcp_client("cloudkms", "v1")
        
        print(f"Scanning for KMS crypto keys...")
        
        # Get all crypto keys
        crypto_keys = []
        # List all locations first
        if location:
            locations = [f"projects/{project_id or kms_client.project}/locations/{location}"]
        else:
            # Get all available locations
            locations_response = kms_client.projects().locations().list(
                name=f"projects/{project_id or kms_client.project}"
            ).execute()
            locations = [loc['name'] for loc in locations_response.get('locations', [])]
        
        for loc in locations:
            try:
                # First list key rings in each location
                key_rings_request = kms_client.projects().locations().keyRings().list(parent=loc)
                
                while key_rings_request is not None:
                    key_rings_response = key_rings_request.execute()
                    
                    for key_ring in key_rings_response.get('keyRings', []):
                        # List crypto keys in each key ring
                        crypto_keys_request = kms_client.projects().locations().keyRings().cryptoKeys().list(
                            parent=key_ring['name']
                        )
                        
                        while crypto_keys_request is not None:
                            crypto_keys_response = crypto_keys_request.execute()
                            
                            for crypto_key in crypto_keys_response.get('cryptoKeys', []):
                                # Extract crypto key details
                                crypto_key_data = {
                                    'name': crypto_key['name'].split('/')[-1],
                                    'name_sanitized': crypto_key['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                    'key_ring': key_ring['name'],
                                    'purpose': crypto_key.get('purpose'),
                                    'create_time': crypto_key.get('createTime'),
                                    'next_rotation_time': crypto_key.get('nextRotationTime'),
                                    'rotation_period': crypto_key.get('rotationPeriod'),
                                    'labels': crypto_key.get('labels', {}),
                                    'import_only': crypto_key.get('importOnly', False),
                                    'destroy_scheduled_duration': crypto_key.get('destroyScheduledDuration'),
                                }
                                
                                # Handle version template
                                if crypto_key.get('versionTemplate'):
                                    crypto_key_data['version_template'] = {
                                        'algorithm': crypto_key['versionTemplate'].get('algorithm'),
                                        'protection_level': crypto_key['versionTemplate'].get('protectionLevel')
                                    }
                                
                                # Handle primary version
                                if crypto_key.get('primary'):
                                    crypto_key_data['primary_version'] = {
                                        'name': crypto_key['primary'].get('name'),
                                        'state': crypto_key['primary'].get('state'),
                                        'create_time': crypto_key['primary'].get('createTime'),
                                        'generate_time': crypto_key['primary'].get('generateTime'),
                                        'destroy_time': crypto_key['primary'].get('destroyTime'),
                                        'destroy_event_time': crypto_key['primary'].get('destroyEventTime'),
                                        'import_job': crypto_key['primary'].get('importJob'),
                                        'import_time': crypto_key['primary'].get('importTime'),
                                        'import_failure_reason': crypto_key['primary'].get('importFailureReason'),
                                        'external_protection_level_options': crypto_key['primary'].get('externalProtectionLevelOptions'),
                                        'reimport_eligible': crypto_key['primary'].get('reimportEligible'),
                                    }
                                
                                crypto_keys.append(crypto_key_data)
                            
                            crypto_keys_request = kms_client.projects().locations().keyRings().cryptoKeys().list_next(
                                previous_request=crypto_keys_request, previous_response=crypto_keys_response
                            )
                    
                    key_rings_request = kms_client.projects().locations().keyRings().list_next(
                        previous_request=key_rings_request, previous_response=key_rings_response
                    )
            except Exception as e:
                print(f"  - Warning: Could not scan location {loc}: {e}")
        
        return crypto_keys
    
    # Use safe operation wrapper
    crypto_keys = safe_gcp_operation(
        _scan_kms_crypto_keys, 
        "Cloud KMS API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_kms_crypto_key.tf"
    generate_tf(crypto_keys, "gcp_kms_crypto_key", output_file)
    print(f"Generated Terraform for {len(crypto_keys)} KMS crypto keys -> {output_file}")
    
    # Generate imports file
    imports = []
    for crypto_key in crypto_keys:
        imports.append({
            "resource_type": "google_kms_crypto_key",
            "resource_name": crypto_key['name_sanitized'],
            "resource_id": f"{crypto_key['key_ring']}/cryptoKeys/{crypto_key['name']}"
        })
    
    if crypto_keys:
        generate_imports_file(
            "gcp_kms_crypto_key",
            crypto_keys,
            "name",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(crypto_keys)} resources")

def list_kms_resources(output_dir: Path):
    """List scanned KMS resources."""
    print("Scanned KMS resources:")
    
    key_ring_file = output_dir / "gcp_kms_key_ring.tf"
    if key_ring_file.exists():
        print(f"  - Key Rings: Check {key_ring_file}")
    
    crypto_key_file = output_dir / "gcp_kms_crypto_key.tf"
    if crypto_key_file.exists():
        print(f"  - Crypto Keys: Check {crypto_key_file}")
    
    if not key_ring_file.exists() and not crypto_key_file.exists():
        print("  - No KMS resources found. Run 'scan-kms' first.")

def import_kms_resource(resource_id: str, resource_type: str, output_dir: Path):
    """Import a specific KMS resource."""
    if resource_type == "key_ring":
        imports_file = output_dir / "gcp_kms_key_ring_imports.tf"
        tf_resource_type = "google_kms_key_ring"
    elif resource_type == "crypto_key":
        imports_file = output_dir / "gcp_kms_crypto_key_imports.tf"
        tf_resource_type = "google_kms_crypto_key"
    else:
        print(f"Invalid resource type: {resource_type}. Use 'key_ring' or 'crypto_key'.")
        return
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-kms' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import(tf_resource_type, resource_id)