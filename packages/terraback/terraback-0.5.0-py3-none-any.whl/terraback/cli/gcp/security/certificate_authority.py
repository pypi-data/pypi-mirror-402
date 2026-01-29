from pathlib import Path
from terraback.cli.gcp.session import get_gcp_client
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.gcp.common.error_handler import safe_gcp_operation

def scan_certificate_authorities(output_dir: Path, project_id: str = None, location: str = None, region: str = None, zone: str = None, **kwargs):
    """
    Scans for Certificate Authorities and generates Terraform code.
    """
    # Use region parameter if location is not provided
    if not location and region:
        location = region
        
    def _scan_certificate_authorities():
        ca_client = get_gcp_client("privateca", "v1")
        
        print(f"Scanning for Certificate Authorities...")
        
        # Get all CAs
        cas = []
        
        try:
            # List all locations first
            if location:
                locations = [f"projects/{project_id or ca_client.project}/locations/{location}"]
            else:
                # Get all available locations
                locations_response = ca_client.projects().locations().list(
                    name=f"projects/{project_id or ca_client.project}"
                ).execute()
                locations = [loc['name'] for loc in locations_response.get('locations', [])]
            
            for loc in locations:
                try:
                    # List CA pools in each location
                    pools_request = ca_client.projects().locations().caPools().list(parent=loc)
                    
                    while pools_request is not None:
                        pools_response = pools_request.execute()
                        
                        for pool in pools_response.get('caPools', []):
                            # List CAs in each pool
                            cas_request = ca_client.projects().locations().caPools().certificateAuthorities().list(
                                parent=pool['name']
                            )
                            
                            while cas_request is not None:
                                cas_response = cas_request.execute()
                                
                                for ca in cas_response.get('certificateAuthorities', []):
                                    # Extract CA details
                                    ca_data = {
                                        'certificate_authority_id': ca['name'].split('/')[-1],
                                        'name_sanitized': ca['name'].split('/')[-1].replace('-', '_').replace('.', '_').lower(),
                                        'location': loc.split('/')[-1],
                                        'pool': pool['name'],
                                        'type': ca.get('type'),
                                        'tier': ca.get('tier'),
                                        'state': ca.get('state'),
                                        'lifetime': ca.get('lifetime'),
                                        'create_time': ca.get('createTime'),
                                        'update_time': ca.get('updateTime'),
                                        'delete_time': ca.get('deleteTime'),
                                        'expire_time': ca.get('expireTime'),
                                        'labels': ca.get('labels', {}),
                                    }
                                    
                                    # Handle config
                                    if ca.get('config'):
                                        ca_data['config'] = {
                                            'subject_config': ca['config'].get('subjectConfig', {}),
                                            'x509_config': ca['config'].get('x509Config', {}),
                                            'public_key': ca['config'].get('publicKey', {}),
                                        }
                                    
                                    # Handle key spec
                                    if ca.get('keySpec'):
                                        ca_data['key_spec'] = {
                                            'cloud_kms_key_version': ca['keySpec'].get('cloudKmsKeyVersion'),
                                            'algorithm': ca['keySpec'].get('algorithm')
                                        }
                                    
                                    # Handle publishing options
                                    if ca.get('publishingOptions'):
                                        ca_data['publishing_options'] = {
                                            'publish_ca_cert': ca['publishingOptions'].get('publishCaCert'),
                                            'publish_crl': ca['publishingOptions'].get('publishCrl'),
                                            'encoding_format': ca['publishingOptions'].get('encodingFormat')
                                        }
                                    
                                    # Handle GCS bucket
                                    ca_data['gcs_bucket'] = ca.get('gcsBucket')
                                    
                                    cas.append(ca_data)
                                
                                cas_request = ca_client.projects().locations().caPools().certificateAuthorities().list_next(
                                    previous_request=cas_request, previous_response=cas_response
                                )
                        
                        pools_request = ca_client.projects().locations().caPools().list_next(
                            previous_request=pools_request, previous_response=pools_response
                        )
                except Exception as e:
                    print(f"  - Warning: Could not scan location {loc}: {e}")
        
        except Exception as e:
            print(f"Error scanning Certificate Authorities: {e}")
            return []
        
        return cas
    
    # Use safe operation wrapper
    cas = safe_gcp_operation(
        _scan_certificate_authorities, 
        "Certificate Authority API", 
        project_id or "default"
    )
    
    output_file = output_dir / "gcp_certificate_authority.tf"
    generate_tf(cas, "gcp_certificate_authority", output_file, provider="gcp")
    print(f"Generated Terraform for {len(cas)} Certificate Authorities -> {output_file}")
    
    # Generate imports file
    if cas:
        generate_imports_file(
            "gcp_certificate_authority",
            cas,
            "certificate_authority_id",
            output_dir,
            provider="gcp"
        )
        print(f"Generated imports file with {len(cas)} resources")

def list_certificate_authorities(output_dir: Path):
    """List scanned Certificate Authorities."""
    tf_file = output_dir / "gcp_certificate_authority.tf"
    if not tf_file.exists():
        print("No Certificate Authorities found. Run 'scan-ca' first.")
        return
    
    print("Scanned Certificate Authorities:")
    print(f"  - Check {tf_file} for details")

def import_certificate_authority(ca_id: str, output_dir: Path):
    """Import a specific Certificate Authority."""
    imports_file = output_dir / "gcp_certificate_authority_imports.tf"
    
    if not imports_file.exists():
        print(f"Imports file not found. Run 'scan-ca' first.")
        return
    
    manager = ImportManager(imports_file)
    manager.run_import("google_privateca_certificate_authority", ca_id)